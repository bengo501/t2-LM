# -*- coding: utf-8 -*-
"""
Etapa 1 — Exploração dos dados.

Carrega catalog.csv e queries.csv (+ val/test), analisa distribuições,
padrões nas queries (abreviações frequentes, categorias) e casos desafiadores.

Uso:
    python src/explore.py
"""
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

DADOS = Path(__file__).resolve().parent.parent / "Dados"


def load_data():
    catalog = pd.read_csv(DADOS / "catalog.csv", dtype=str)
    queries = pd.read_csv(DADOS / "queries.csv", dtype=str)
    val = pd.read_csv(DADOS / "queries_val.csv", dtype=str)
    test = pd.read_csv(DADOS / "queries_test.csv", dtype=str)
    return catalog, queries, val, test


def main():
    catalog, queries, val, test = load_data()

    print("=" * 70)
    print("TAMANHO DOS CONJUNTOS")
    print("=" * 70)
    print(f"catalog.csv      : {len(catalog):>6} produtos")
    print(f"queries.csv      : {len(queries):>6} consultas (sem rótulo)")
    print(f"queries_val.csv  : {len(val):>6} consultas anotadas")
    print(f"queries_test.csv : {len(test):>6} consultas anotadas")

    print()
    print("=" * 70)
    print("CATÁLOGO")
    print("=" * 70)
    print(f"product_id únicos   : {catalog['product_id'].nunique()}")
    print(f"product_name únicos : {catalog['product_name'].nunique()}")
    print(f"Marcas únicas       : {catalog['brand_name'].nunique()}")
    print(f"Nulos por coluna    :\n{catalog.isna().sum().to_string()}")
    dup_names = catalog[catalog.duplicated('product_name', keep=False)]
    print(f"Nomes de produto duplicados (ambiguidade!): {dup_names['product_name'].nunique()} "
          f"nomes em {len(dup_names)} linhas")
    if len(dup_names):
        print("Exemplos de nomes duplicados:")
        for name, grp in list(dup_names.groupby('product_name'))[:5]:
            print(f"  '{name}' -> ids {list(grp['product_id'])}")

    print(f"\nTop 15 marcas:\n{catalog['brand_name'].value_counts().head(15).to_string()}")

    # primeira palavra do nome ~ categoria do produto
    cat_first = catalog['product_name'].str.split().str[0].str.lower()
    print(f"\nTop 15 'categorias' (1ª palavra do nome):\n{cat_first.value_counts().head(15).to_string()}")

    print()
    print("=" * 70)
    print("QUERIES (não rotuladas)")
    print("=" * 70)
    print(f"Consultas únicas : {queries['text'].nunique()} de {len(queries)}")
    print(f"matched_id vazio : {queries['matched_id'].isna().all()}")
    qlen = queries['text'].str.len()
    print(f"Comprimento (caracteres): min={qlen.min()} mediana={qlen.median():.0f} max={qlen.max()}")
    qtok = queries['text'].str.split().str.len()
    print(f"Comprimento (tokens)    : min={qtok.min()} mediana={qtok.median():.0f} max={qtok.max()}")

    # tokens frequentes em caixa alta / padrões de embalagem
    all_text = " ".join(queries['text'].astype(str))
    tokens = re.findall(r"\S+", all_text.upper())
    cnt = Counter(tokens)
    print(f"\nTop 30 tokens mais frequentes nas queries:")
    for tok, c in cnt.most_common(30):
        print(f"  {tok:<15} {c}")

    pack = [t for t in tokens if re.fullmatch(r"C/\d+|\d+X\d+\w*|CX\d*|FD\d*|PCT|UND?|UNID", t)]
    print(f"\nTokens de embalagem/quantidade (C/6, 12X..., UND...): {len(pack)} ocorrências")
    print(Counter(pack).most_common(15))

    print()
    print("=" * 70)
    print("VALIDAÇÃO / TESTE — cobertura no catálogo")
    print("=" * 70)
    ids = set(catalog['product_id'])
    for name, df in [("val", val), ("test", test)]:
        df = df.copy()
        df['matched_id'] = df['matched_id'].fillna("")
        in_cat = df['matched_id'].isin(ids).sum()
        empty = (df['matched_id'] == "").sum()
        no_match = len(df) - in_cat - empty
        print(f"queries_{name}: {in_cat} com id no catálogo | {empty} vazios | "
              f"{no_match} com id FORA do catálogo (NO_MATCH)")
        if no_match:
            fora = df[~df['matched_id'].isin(ids) & (df['matched_id'] != "")]
            print(f"  Exemplos NO_MATCH ({name}):")
            for _, r in fora.head(5).iterrows():
                print(f"    '{r['text']}' -> {r['matched_id']}")

    # sobreposição de estilo entre queries.csv e val/test
    print()
    print("=" * 70)
    print("ESTILO val/test vs queries.csv")
    print("=" * 70)
    print("Exemplos de queries.csv :", queries['text'].head(3).tolist())
    print("Exemplos de val         :", val['text'].head(3).tolist())
    inter = set(queries['text']) & set(val['text']) | set(queries['text']) & set(test['text'])
    print(f"Textos de val/test que também aparecem em queries.csv: {len(inter)}")

    # queries de val cujo texto contém marca que não está no catálogo, etc.
    upper_ratio_q = (queries['text'].str.isupper()).mean()
    upper_ratio_v = (val['text'].str.isupper()).mean()
    print(f"% de queries 100% MAIÚSCULAS — queries.csv: {upper_ratio_q:.1%} | val: {upper_ratio_v:.1%}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
