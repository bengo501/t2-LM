# -*- coding: utf-8 -*-
"""
Etapa 6 — Análise qualitativa.

Gera, a partir dos arquivos results/detalhes_*.json produzidos pelas duas
abordagens, um relatório em Markdown com:
  - exemplos de acertos;
  - exemplos de erros, com diagnóstico heurístico do motivo
    (tamanho/quantidade errada, marca errada, variante/sabor errado);
  - casos ambíguos (nomes duplicados no catálogo ou top-2 muito próximos);
  - comportamento em casos NO_MATCH (queries de queries.csv sem produto
    correspondente no catálogo) e proposta de limiar de rejeição.

Uso:
    python src/qualitative.py --split test --classic bm25 --deep deep_hybrid
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocess import normalize

ROOT = Path(__file__).resolve().parent.parent
DADOS = ROOT / "Dados"
RESULTS = ROOT / "results"


def load_details(method, split):
    path = RESULTS / f"detalhes_{method}_{split}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def qty_tokens(text):
    return set(re.findall(r"\d+(?:\.\d+)?(?:ml|l|g|kg|mg)\b", normalize(text)))


def diagnose(d):
    """Heurística do motivo do erro a partir do gold e do top-1."""
    gold, pred = d["gold_name"], d["top"][0]["name"] if "top" in d else d["top5"][0]["name"]
    g_qty, p_qty = qty_tokens(gold), qty_tokens(pred)
    g_tok = set(normalize(gold).split())
    p_tok = set(normalize(pred).split())
    if g_qty != p_qty and (g_tok - {*g_qty}) & (p_tok - {*p_qty}):
        return "tamanho/quantidade errada"
    inter = g_tok & p_tok
    if len(inter) >= max(2, len(g_tok) // 2):
        return "variante/sabor/versão errada do mesmo produto"
    return "produto diferente (similaridade lexical enganosa)"


def section_hits_errors(details, name, n=5):
    hits = [d for d in details if d["top5"] and d["top5"][0]["id"] == d["gold_id"]]
    errs = [d for d in details if not d["top5"] or d["top5"][0]["id"] != d["gold_id"]]
    out = [f"\n## {name}: {len(hits)} acertos, {len(errs)} erros (P@1={len(hits)/len(details):.3f})\n"]
    out.append("### Exemplos de acertos\n")
    out.append("| Query | Produto encontrado | Score |")
    out.append("|---|---|---|")
    for d in hits[:n]:
        t = d["top5"][0]
        out.append(f"| {d['text']} | {t['name']} | {t['score']:.3f} |")
    out.append("\n### Erros (todos) com diagnóstico\n")
    out.append("| Query | Esperado | Obtido (top-1) | Posição do correto | Diagnóstico |")
    out.append("|---|---|---|---|---|")
    for d in errs:
        ids = [t["id"] for t in d["top5"]]
        pos = ids.index(d["gold_id"]) + 1 if d["gold_id"] in ids else ">5"
        out.append(f"| {d['text']} | {d['gold_name']} | {d['top5'][0]['name']} "
                   f"| {pos} | {diagnose({'gold_name': d['gold_name'], 'top5': d['top5']})} |")
    return out, hits, errs


def section_ambiguous(details, catalog, n=8):
    dup_names = set(catalog[catalog.duplicated("product_name", keep=False)]["product_name"])
    out = ["\n## Casos ambíguos\n"]
    out.append("Queries cujo produto correto tem nome duplicado no catálogo (ids diferentes, "
               "mesmo nome) ou cujo top-2 tem scores quase idênticos:\n")
    out.append("| Query | Top-1 | Top-2 | Δ score | Observação |")
    out.append("|---|---|---|---|---|")
    count = 0
    for d in details:
        if len(d["top5"]) < 2 or count >= n:
            continue
        t1, t2 = d["top5"][0], d["top5"][1]
        delta = t1["score"] - t2["score"]
        dup = t1["name"] in dup_names or t1["name"] == t2["name"]
        if dup or delta < 0.01:
            obs = "nome duplicado no catálogo" if dup else "scores quase empatados"
            out.append(f"| {d['text']} | {t1['name']} | {t2['name']} | {delta:.4f} | {obs} |")
            count += 1
    if count == 0:
        out.append("| — | — | — | — | nenhum caso encontrado |")
    return out


def section_no_match(classic_details):
    """Analisa scores para discutir NO_MATCH e propõe limiar de rejeição."""
    correct = [d["top5"][0]["score"] for d in classic_details
               if d["top5"] and d["top5"][0]["id"] == d["gold_id"]]
    wrong = [d["top5"][0]["score"] for d in classic_details
             if d["top5"] and d["top5"][0]["id"] != d["gold_id"]]
    out = ["\n## Casos NO_MATCH\n"]
    out.append("Os conjuntos val/test não contêm queries sem correspondência no catálogo "
               "(todos os matched_id existem). Para discutir o comportamento em NO_MATCH, "
               "analisamos os *scores* do top-1: um sistema em produção deve rejeitar "
               "matches com score abaixo de um limiar.\n")
    if correct:
        s = pd.Series(correct)
        out.append(f"- Score top-1 quando o match está **correto**: "
                   f"média {s.mean():.3f}, p5 {s.quantile(0.05):.3f}, mín {s.min():.3f}")
    if wrong:
        s = pd.Series(wrong)
        out.append(f"- Score top-1 quando o match está **errado**: "
                   f"média {s.mean():.3f}, máx {s.max():.3f}")
    out.append("\nExemplos de queries reais de queries.csv sem produto no catálogo "
               "(verificadas manualmente) e o que cada abordagem devolve estão na "
               "seção de NO_MATCH do relatório (script run_no_match.py).")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["val", "test"], default="test")
    ap.add_argument("--classic", default="bm25")
    ap.add_argument("--deep", default="deep_hybrid")
    args = ap.parse_args()

    catalog = pd.read_csv(DADOS / "catalog.csv", dtype=str)
    out = [f"# Análise qualitativa — split: {args.split}\n"]

    classic = load_details(args.classic, args.split)
    deep = load_details(args.deep, args.split)

    sec, _, errs_c = section_hits_errors(classic, f"Abordagem 1 ({args.classic})")
    out += sec
    sec, _, errs_d = section_hits_errors(deep, f"Abordagem 2 ({args.deep})")
    out += sec

    # onde uma abordagem acerta e a outra erra
    c_err_texts = {d["text"] for d in errs_c}
    d_err_texts = {d["text"] for d in errs_d}
    only_c = c_err_texts - d_err_texts
    only_d = d_err_texts - c_err_texts
    out.append("\n## Comparação direta\n")
    out.append(f"- Erros só da Abordagem 1 (deep acertou): {len(only_c)}")
    for t in list(only_c)[:6]:
        out.append(f"  - {t}")
    out.append(f"- Erros só da Abordagem 2 (clássico acertou): {len(only_d)}")
    for t in list(only_d)[:6]:
        out.append(f"  - {t}")
    out.append(f"- Erros em comum: {len(c_err_texts & d_err_texts)}")

    out += section_ambiguous(classic, catalog)
    out += section_no_match(classic)

    RESULTS.mkdir(exist_ok=True)
    outfile = RESULTS / f"analise_qualitativa_{args.split}.md"
    outfile.write_text("\n".join(out), encoding="utf-8")
    print(f"Análise salva em {outfile}")
    print("\n".join(out[:40]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
