# -*- coding: utf-8 -*-
"""
Preenchimento de queries.csv — "matched_id (a ser preenchido pelo grupo)".

Aplica a melhor variante selecionada na validação (TF-IDF de caracteres 3-5)
em lote sobre as 16.441 queries e grava results/queries_preenchido.csv com:
  text        texto original da query (inalterado)
  matched_id  product_id do produto ranqueado em 1º lugar
  score       similaridade de cosseno do top-1 (0 a 1)

O score permite aplicar um limiar de rejeição, mas ele deve ser calibrado por
estilo de query: nas queries descritivas (estilo val/test) os matches corretos
têm score >= 0.786, enquanto nas queries abreviadas de queries.csv um match
correto pode ficar em ~0.73 ("FANTA LARANJA 2L C/6") e NO_MATCHes verificados
ficam em ~0.41-0.43 ("MORMAII LATA BRANCO C/6", "SKOL LATA 350ml C/12" — não
há Skol comum neste catálogo, só Skol Beats). Um limiar de ~0.55 separa
razoavelmente os dois regimes no estilo abreviado; o ideal é calibrar com uma
amostra rotulada manualmente.

O arquivo original Dados/queries.csv NÃO é modificado.

Uso:
    python src/fill_queries.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize as l2_normalize

sys.path.insert(0, str(Path(__file__).resolve().parent))
from approach1_classic import load_catalog
from preprocess import normalize

ROOT = Path(__file__).resolve().parent.parent
DADOS = ROOT / "Dados"
RESULTS = ROOT / "results"

CHUNK = 2000  # queries por lote (controla o uso de memória)


def main():
    catalog = load_catalog(use_brand=True)
    queries = pd.read_csv(DADOS / "queries.csv", dtype=str)

    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
    doc_matrix = l2_normalize(vec.fit_transform(catalog["doc"]))
    ids = np.array(catalog["product_id"])

    print(f"Preenchendo {len(queries)} queries com TF-IDF char (3-5)...")
    t0 = time.perf_counter()
    q_norm = [normalize(t) for t in queries["text"]]
    matched, scores = [], []
    for start in range(0, len(queries), CHUNK):
        q_matrix = l2_normalize(vec.transform(q_norm[start:start + CHUNK]))
        sims = (q_matrix @ doc_matrix.T).toarray()   # cosseno (linhas L2-normalizadas)
        best = sims.argmax(axis=1)
        matched.extend(ids[best])
        scores.extend(sims[np.arange(len(best)), best])
        print(f"  {min(start + CHUNK, len(queries))}/{len(queries)}", flush=True)
    elapsed = time.perf_counter() - t0

    out = pd.DataFrame({
        "text": queries["text"],
        "matched_id": matched,
        "score": np.round(scores, 4),
    })
    RESULTS.mkdir(exist_ok=True)
    outfile = RESULTS / "queries_preenchido.csv"
    out.to_csv(outfile, index=False, encoding="utf-8")

    print(f"\nConcluído em {elapsed:.1f}s ({len(queries)/elapsed:.0f} queries/s)")
    print(f"Salvo em {outfile}")
    print(f"\nDistribuição do score top-1:")
    print(out["score"].describe().round(3).to_string())
    for limiar in (0.45, 0.55, 0.65):
        n = (out["score"] < limiar).sum()
        print(f"Abaixo de {limiar:.2f} (possível NO_MATCH): {n} ({n/len(out):.1%})")
    print("\nNota: o limiar deve ser calibrado por estilo de query; ver docstring.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
