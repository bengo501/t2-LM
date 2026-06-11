# -*- coding: utf-8 -*-
"""
Etapa 6 (complemento) — Comportamento das abordagens em casos NO_MATCH.

Seleciona queries reais de queries.csv cujas marcas comprovadamente NÃO
existem no catálogo (Qualitá, Taeq, Swift, Mormaii, Carnilove...) e mostra o
top-3 devolvido por cada abordagem, com os scores. Como nenhuma das abordagens
tem mecanismo nativo de rejeição, a saída sempre aponta algum produto — a
análise mostra que o score do top-1 nesses casos é bem mais baixo do que o
score típico de um match correto, viabilizando um limiar de rejeição.

Uso:
    python src/run_no_match.py
"""
import json
import sys
from pathlib import Path

import torch  # noqa: F401  (importar antes de pandas; ver approach2_deep.py)
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from approach1_classic import load_catalog, make_tfidf_ranker
from approach2_deep import catalog_embeddings, get_model, make_hybrid_ranker
from evaluate import K

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

# Queries reais de queries.csv de marcas/produtos ausentes do catálogo
NO_MATCH_QUERIES = [
    "MORMAII LATA BRANCO C/6",
    "Limpador para Casa Perfumado QUALITÁ Lavanda 2 litros",
    "Farinha de Chia Taeq Pouch 150g",
    "Rabo de Bovino Congelado SWIFT 2Kg",
    "Ração para Cães Carnilove Adulto Fresh Chicken & Rabbit 1,5kg",
    "CACHACA COBICADA UMBURANA 250ml C/6",
    "CHICLETE BUZZY ROSA MORANGO",
]
# Controle: queries com produto no catálogo (do conjunto de validação)
CONTROL_QUERIES = [
    "Café Solúvel Granulado Forte Nescafé Tradição Sachê 40g",
    "Lava-Roupas Líquido Lavanda Omo Sachê 900ml Refil",
]


def main():
    catalog = load_catalog(use_brand=True)
    id2name = dict(zip(catalog["product_id"], catalog["product_name"]))

    classic = make_tfidf_ranker(catalog, analyzer="char")
    model = get_model()
    emb = catalog_embeddings(model, catalog["doc"].tolist())
    deep = make_hybrid_ranker(model, catalog, emb)

    # limiar de referência: score top-1 dos matches corretos na validação
    val_details = json.loads(
        (RESULTS / "detalhes_tfidf_char_val.json").read_text(encoding="utf-8"))
    correct_scores = pd.Series([
        d["top5"][0]["score"] for d in val_details
        if d["top5"] and d["top5"][0]["id"] == d["gold_id"]])

    out = ["# Comportamento em casos NO_MATCH\n"]
    out.append(f"Referência (validação, tfidf_char): score top-1 dos matches corretos tem "
               f"média {correct_scores.mean():.3f} e percentil 5 = "
               f"{correct_scores.quantile(0.05):.3f}.\n")

    for grupo, queries in [("Queries NO_MATCH (produto não existe no catálogo)",
                            NO_MATCH_QUERIES),
                           ("Queries de controle (produto existe)", CONTROL_QUERIES)]:
        out.append(f"\n## {grupo}\n")
        for q in queries:
            out.append(f"\n**{q}**\n")
            out.append("| Abordagem | Top-3 | Scores |")
            out.append("|---|---|---|")
            for nome, ranker in [("tfidf_char", classic), ("deep_hybrid", deep)]:
                top = ranker(q)[:3]
                nomes = "; ".join(id2name.get(pid, "?") for pid, _ in top)
                scores = ", ".join(f"{s:.3f}" for _, s in top)
                out.append(f"| {nome} | {nomes} | {scores} |")

    RESULTS.mkdir(exist_ok=True)
    outfile = RESULTS / "no_match.md"
    outfile.write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))
    print(f"\nSalvo em {outfile}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
