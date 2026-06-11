# -*- coding: utf-8 -*-
"""
Abordagem 2 — Deep Learning: embeddings semânticos com Sentence-Transformers.

Modelo: paraphrase-multilingual-MiniLM-L12-v2 (multilíngue, roda local na CPU,
gratuito — sem necessidade de API key).

Variações avaliadas:
  - dense  : embeddings do catálogo inteiro + similaridade de cosseno (busca densa)
  - hybrid : BM25 seleciona top-50 candidatos, o modelo neural re-ranqueia
             (estratégia recomendada no enunciado: reduz custo e melhora qualidade)

Os embeddings do catálogo são cacheados em cache/ para não recodificar 14k
produtos a cada execução.

Uso:
    python src/approach2_deep.py --split val             # dense + hybrid
    python src/approach2_deep.py --split test --variant hybrid
    python src/approach2_deep.py --split val --raw-text  # sem pré-processamento
"""
import argparse
import hashlib
import sys
import time
from pathlib import Path

# No Windows desta máquina, importar pandas antes do torch quebra o carregamento
# da DLL c10.dll (conflito de runtime). O torch precisa vir primeiro.
import torch  # noqa: F401  (precisa ser importado antes de pandas)

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from approach1_classic import load_catalog, save_details
from bm25 import BM25
from evaluate import evaluate_ranker, fmt
from preprocess import normalize, tokenize

ROOT = Path(__file__).resolve().parent.parent
DADOS = ROOT / "Dados"
CACHE = ROOT / "cache"
RESULTS = ROOT / "results"

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME, device="cpu")


def catalog_embeddings(model, docs):
    """Codifica (com cache em disco) todos os documentos do catálogo."""
    CACHE.mkdir(exist_ok=True)
    key = hashlib.md5(("\n".join(docs) + MODEL_NAME).encode("utf-8")).hexdigest()[:12]
    path = CACHE / f"catalog_emb_{key}.npy"
    if path.exists():
        return np.load(path)
    print(f"Codificando {len(docs)} produtos do catálogo (uma única vez)...")
    t0 = time.perf_counter()
    emb = model.encode(docs, batch_size=256, show_progress_bar=True,
                       normalize_embeddings=True, convert_to_numpy=True)
    print(f"Catálogo codificado em {time.perf_counter() - t0:.1f}s")
    np.save(path, emb)
    return emb


def make_dense_ranker(model, catalog, emb):
    ids = catalog["product_id"].tolist()

    def rank(text, k=5):
        q = model.encode([normalize(text)], normalize_embeddings=True,
                         convert_to_numpy=True)[0]
        sims = emb @ q                      # cosseno (vetores já normalizados)
        top = np.argsort(-sims, kind="stable")[:k]   # desempate determinístico
        return [(ids[i], float(sims[i])) for i in top]

    return rank


def make_hybrid_ranker(model, catalog, emb, n_candidates=50):
    """BM25 filtra n_candidates; o modelo neural decide o ranking final."""
    ids = catalog["product_id"].tolist()
    bm25 = BM25([d.split() for d in catalog["doc"]])

    def rank(text, k=5):
        cand = [i for i, _ in bm25.topk(tokenize(text), n_candidates)]
        q = model.encode([normalize(text)], normalize_embeddings=True,
                         convert_to_numpy=True)[0]
        sims = emb[cand] @ q
        order = np.argsort(-sims, kind="stable")[:k]  # desempate determinístico
        return [(ids[cand[i]], float(sims[i])) for i in order]

    return rank


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["val", "test"], default="val")
    ap.add_argument("--variant", choices=["dense", "hybrid", "all"], default="all")
    ap.add_argument("--raw-text", action="store_true",
                    help="codifica o texto cru, sem o pré-processamento")
    args = ap.parse_args()

    queries = pd.read_csv(DADOS / f"queries_{args.split}.csv", dtype=str)
    catalog = load_catalog(use_brand=True)
    if args.raw_text:
        catalog["doc"] = catalog["doc_raw"]
        global normalize
        normalize = lambda t: str(t)  # noqa: E731

    print(f"[abordagem 2] split={args.split}  modelo={MODEL_NAME}  "
          f"texto={'cru' if args.raw_text else 'pré-processado'}\n")
    model = get_model()
    emb = catalog_embeddings(model, catalog["doc"].tolist())

    variants = ["dense", "hybrid"] if args.variant == "all" else [args.variant]
    for v in variants:
        ranker = (make_dense_ranker(model, catalog, emb) if v == "dense"
                  else make_hybrid_ranker(model, catalog, emb))
        metrics, details, _ = evaluate_ranker(ranker, queries)
        print(f"{v:<7} {fmt(metrics)}")
        suffix = "_raw" if args.raw_text else ""
        save_details(details, catalog,
                     RESULTS / f"detalhes_deep_{v}{suffix}_{args.split}.json")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
