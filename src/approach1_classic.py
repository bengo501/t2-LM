# -*- coding: utf-8 -*-
"""
Abordagem 1 — NLP Clássico: TF-IDF (cosseno) e BM25.

Variações avaliadas:
  - tfidf_word : TF-IDF de palavras (uni+bigramas) + similaridade de cosseno
  - tfidf_char : TF-IDF de n-gramas de caracteres (3 a 5, char_wb) + cosseno
  - bm25       : BM25 (implementação própria em src/bm25.py)

Uso:
    python src/approach1_classic.py --split val            # todas as variações
    python src/approach1_classic.py --split test --method bm25
    python src/approach1_classic.py --split val --no-brand # indexa só o nome
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bm25 import BM25
from evaluate import evaluate_ranker, fmt
from preprocess import normalize, tokenize

ROOT = Path(__file__).resolve().parent.parent
DADOS = ROOT / "Dados"
RESULTS = ROOT / "results"


def load_catalog(use_brand=True):
    catalog = pd.read_csv(DADOS / "catalog.csv", dtype=str)
    if use_brand:
        # acrescenta a marca quando ela ainda não aparece no nome do produto
        def doc(row):
            name, brand = row["product_name"], str(row["brand_name"])
            if brand and brand.lower() not in name.lower():
                return f"{name} {brand}"
            return name
        catalog["doc_raw"] = catalog.apply(doc, axis=1)
    else:
        catalog["doc_raw"] = catalog["product_name"]
    catalog["doc"] = catalog["doc_raw"].map(normalize)
    return catalog


def make_tfidf_ranker(catalog, analyzer="word"):
    if analyzer == "word":
        vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    else:
        vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
    doc_matrix = vec.fit_transform(catalog["doc"])
    ids = catalog["product_id"].tolist()
    names = catalog["product_name"].tolist()

    def rank(text, k=5):
        q = vec.transform([normalize(text)])
        sims = cosine_similarity(q, doc_matrix).ravel()
        # ordenação estável: empates são resolvidos pela ordem do catálogo,
        # garantindo resultados determinísticos e reprodutíveis
        top = np.argsort(-sims, kind="stable")[:k]
        return [(ids[i], float(sims[i])) for i in top]

    rank.names = names
    return rank


def make_bm25_ranker(catalog, k1=1.5, b=0.75):
    docs = [d.split() for d in catalog["doc"]]
    bm25 = BM25(docs, k1=k1, b=b)
    ids = catalog["product_id"].tolist()
    names = catalog["product_name"].tolist()

    def rank(text, k=5):
        return [(ids[i], s) for i, s in bm25.topk(tokenize(text), k)]

    rank.names = names
    rank.bm25 = bm25
    return rank


def save_details(details, catalog, outfile):
    """Salva o top-5 de cada query (com nomes) para a análise qualitativa."""
    id2name = dict(zip(catalog["product_id"], catalog["product_name"]))
    rows = []
    for d in details:
        rows.append({
            "text": d["text"],
            "gold_id": d["gold"],
            "gold_name": id2name.get(d["gold"], "<FORA DO CATALOGO>"),
            "top5": [
                {"id": pid, "name": id2name.get(pid, "?"), "score": round(score, 4)}
                for pid, score in d["top"]
            ],
        })
    RESULTS.mkdir(exist_ok=True)
    outfile.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["val", "test"], default="val")
    ap.add_argument("--method", choices=["tfidf_word", "tfidf_char", "bm25", "all"],
                    default="all")
    ap.add_argument("--no-brand", action="store_true",
                    help="indexa apenas product_name (sem brand_name)")
    args = ap.parse_args()

    queries = pd.read_csv(DADOS / f"queries_{args.split}.csv", dtype=str)
    catalog = load_catalog(use_brand=not args.no_brand)
    print(f"[abordagem 1] split={args.split}  catálogo={len(catalog)}  "
          f"brand={'não' if args.no_brand else 'sim'}\n")

    methods = ["tfidf_word", "tfidf_char", "bm25"] if args.method == "all" else [args.method]
    for m in methods:
        if m == "bm25":
            ranker = make_bm25_ranker(catalog)
        else:
            ranker = make_tfidf_ranker(catalog, analyzer="word" if m == "tfidf_word" else "char")
        metrics, details, _ = evaluate_ranker(ranker, queries)
        print(f"{m:<11} {fmt(metrics)}")
        save_details(details, catalog,
                     RESULTS / f"detalhes_{m}_{args.split}.json")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
