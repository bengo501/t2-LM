# -*- coding: utf-8 -*-
"""
Gera T2_Matching_Produtos.ipynb embutindo o código dos módulos de src/
(para manter notebook e scripts idênticos) + células de orquestração.

Uso:  python tools/build_notebook.py
"""
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"


def upto(path, marker):
    text = (SRC / path).read_text(encoding="utf-8")
    return text.split(marker)[0].rstrip()


def between(path, start, stop):
    text = (SRC / path).read_text(encoding="utf-8")
    return text[text.index(start):text.index(stop)].rstrip()


md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell

cells = []

# ---------------------------------------------------------------- capa
cells.append(md("""\
# T2 — Matching de Produtos
**Aprendizado de Máquina — Prof. Me. Otávio Parraga**

**Integrantes:** _\\<preencher nomes e matrículas\\>_

Dado um texto de consulta heterogêneo (ex.: `FANTA LARANJA 2L C/6`), o sistema encontra o
produto correspondente no catálogo normalizado (`Dados/catalog.csv`, 14.206 produtos).

Duas abordagens são implementadas e comparadas:

| Abordagem | Técnica |
|---|---|
| **1 — NLP Clássico** | TF-IDF (palavras e n-gramas de caracteres) com cosseno + **BM25 implementado do zero** |
| **2 — Deep Learning** | Embeddings semânticos (`paraphrase-multilingual-MiniLM-L12-v2`, local/CPU), variantes densa e híbrida (BM25 top-50 → re-rank neural) |

Métricas: **P@1**, **MRR@5** e **R@5**, calculadas em `queries_val.csv` (desenvolvimento) e,
uma única vez ao final, em `queries_test.csv` (definitivas).

> Este notebook é autocontido (não depende de `src/`), mas o código é o mesmo dos scripts
> em `src/`, que continuam sendo a forma recomendada de reprodução em lote."""))

# ---------------------------------------------------------------- setup
cells.append(md("## 0. Setup\n\nImports e caminhos. **Atenção:** nesta máquina o `torch` "
                "precisa ser importado **antes** do `pandas` (conflito de DLL no Windows)."))
cells.append(code("""\
import torch  # importar ANTES de pandas (conflito de DLL c10.dll no Windows)

import hashlib, json, math, re, time, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize as l2_normalize

ROOT = Path.cwd()                 # executar o notebook a partir da raiz do projeto
DADOS, CACHE, RESULTS = ROOT / "Dados", ROOT / "cache", ROOT / "results"
RESULTS.mkdir(exist_ok=True)
pd.set_option("display.max_colwidth", 90)
print("torch", torch.__version__, "| pandas", pd.__version__)"""))

# ---------------------------------------------------------------- exploração
cells.append(md("""## 1. Exploração dos dados

Carregamos os quatro CSVs **sempre com `dtype=str`** — os `product_id` são códigos EAN com
zero à esquerda (`07891...`) e seriam corrompidos se lidos como inteiros."""))
cells.append(code("""\
catalog = pd.read_csv(DADOS / "catalog.csv", dtype=str)
queries = pd.read_csv(DADOS / "queries.csv", dtype=str)
val     = pd.read_csv(DADOS / "queries_val.csv", dtype=str)
test    = pd.read_csv(DADOS / "queries_test.csv", dtype=str)

print(f"catalog={len(catalog)}  queries={len(queries)}  val={len(val)}  test={len(test)}")
catalog.head(3)"""))
cells.append(code("""\
# Catálogo: marcas, "categorias" (1ª palavra) e nomes duplicados (ambiguidade!)
dup = catalog[catalog.duplicated("product_name", keep=False)]
print(f"Marcas únicas: {catalog['brand_name'].nunique()}")
print(f"Nomes duplicados sob ids diferentes: {dup['product_name'].nunique()} nomes / {len(dup)} linhas")
display(catalog["product_name"].str.split().str[0].str.lower().value_counts().head(10).to_frame("qtde"))
dup.sort_values("product_name").head(6)"""))
cells.append(code("""\
# Queries: comprimento e tokens de embalagem/quantidade (C/6, 12X..., UND)
tok = queries["text"].str.split().str.len()
print(f"Tokens por query: mediana={tok.median():.0f}  min={tok.min()}  max={tok.max()}")
pack = re.findall(r"\\b(?:C/\\d+|\\d+X\\d+\\w*|CX\\d*|FD\\d*|PCT|UND?|UNID)\\b",
                  " ".join(queries["text"]).upper())
print(f"Tokens de embalagem: {len(pack)} ocorrências — {Counter(pack).most_common(8)}")

# Cobertura de val/test no catálogo (há NO_MATCH rotulado?)
ids = set(catalog["product_id"])
print(f"val com id no catálogo : {val['matched_id'].isin(ids).sum()}/{len(val)}")
print(f"test com id no catálogo: {test['matched_id'].isin(ids).sum()}/{len(test)}")"""))
cells.append(md("""**Observações da exploração:**
- val/test estão 100% cobertos pelo catálogo → não há NO_MATCH rotulado (tratamos NO_MATCH na Seção 7);
- o estilo de val/test é descritivo (`"Sabonete Líquido Buquê de Jasmim Lux..."`), enquanto
  `queries.csv` é abreviado e ruidoso (`"FINI MINI BANANAS 12X15 GR Und"`);
- `queries.csv` contém famílias inteiras de NO_MATCH: as marcas **Qualitá** (1.234 queries),
  **Taeq**, **Swift**, **Carnilove** e **Mormaii** não existem no catálogo — e não há
  "Cerveja skol lata 350ml" neste catálogo (só Skol Beats);
- o catálogo tem 29 nomes duplicados sob ids distintos → ambiguidade irredutível por texto."""))

# ---------------------------------------------------------------- pré-processamento
cells.append(md("""## 2. Pré-processamento textual (Etapa 1.1)

Normalização aplicada **tanto às queries quanto ao catálogo**. Decisões principais:
- `12X350ML` → `350ml` (mantém o tamanho unitário, descarta a multiplicidade);
- `2L`, `2 litros` → `2l` (forma canônica de unidades);
- **mantemos "sem"** (não como stopword): é discriminativo em "sem açúcar/gás/lactose";
- dicionário de abreviações **conservador**: `COND` (condensado×condicionador) e `SAB`
  (sabão×sabonete) ficam de fora de propósito — expansão errada induz match errado."""))
cells.append(code(upto("preprocess.py", 'if __name__') + """\n\n
exemplos = ["COCA COLA 1L C/6", "MONSTER BRANCO S/ACUCAR C/6 UNID",
            "FINI MINI BANANAS 12X15 GR Und", "CERV HEINEKEN LONG NECK 330ML CX24",
            "Suco de uva orgânico aliança 1 litro", "1,5L AGUA C/ GAS"]
pd.DataFrame({"original": exemplos, "normalizado": [normalize(e) for e in exemplos]})"""))

# ---------------------------------------------------------------- métricas
cells.append(md("""## 3. Métricas de avaliação

P@1 (produto correto em 1º), MRR@5 (crédito parcial por posição, 1/rank, 0 se fora do top-5)
e R@5 (correto em alguma das 5 primeiras posições), conforme o enunciado."""))
cells.append(code((SRC / "evaluate.py").read_text(encoding="utf-8")
                  .replace('# -*- coding: utf-8 -*-\n', '').strip()))

# ---------------------------------------------------------------- abordagem 1
cells.append(md("""## 4. Abordagem 1 — NLP Clássico

### 4.1 BM25 (implementação própria, com índice invertido)"""))
cells.append(code((SRC / "bm25.py").read_text(encoding="utf-8")
                  .replace('# -*- coding: utf-8 -*-\n', '').strip()))
cells.append(md("""### 4.2 Pipelines TF-IDF e BM25

O catálogo é indexado como `product_name` + `brand_name` (quando a marca ainda não aparece
no nome). Em empates de score, a ordenação **estável** garante desempate determinístico
pela ordem do catálogo (reprodutibilidade)."""))
cells.append(code(between("approach1_classic.py", "def load_catalog", "def save_details")))
cells.append(md("### 4.3 Avaliação na validação (250 queries)"))
cells.append(code("""\
catalogo = load_catalog(use_brand=True)
id2name = dict(zip(catalogo["product_id"], catalogo["product_name"]))

rankers_classicos = {
    "tfidf_word": make_tfidf_ranker(catalogo, analyzer="word"),
    "tfidf_char": make_tfidf_ranker(catalogo, analyzer="char"),
    "bm25":       make_bm25_ranker(catalogo),
}
det_val = {}
for nome, rk in rankers_classicos.items():
    m, det_val[nome], _ = evaluate_ranker(rk, val)
    print(f"{nome:<11} {fmt(m)}")"""))
cells.append(md("""**Ablações testadas na validação** (decididas aqui, nunca no teste):
indexar sem a marca não alterou nenhuma métrica; BM25 com k₁/b padrão (1,5/0,75) ficou a
0,8 p.p. do TF-IDF-char com custo ~40× menor. **Variante selecionada: TF-IDF de
caracteres (3–5)** — n-gramas de caracteres são robustos a erros ortográficos e abreviações
residuais."""))

# ---------------------------------------------------------------- abordagem 2
cells.append(md("""## 5. Abordagem 2 — Deep Learning (embeddings semânticos)

Modelo `paraphrase-multilingual-MiniLM-L12-v2` (Sentence-Transformers), local na CPU,
**sem chave de API**. O catálogo é codificado uma única vez (cache em `cache/`).
Variantes: **densa** (cosseno contra os 14.206 produtos) e **híbrida** (BM25 filtra 50
candidatos → o modelo neural decide o ranking final — estratégia recomendada no enunciado)."""))
cells.append(code(between("approach2_deep.py", 'MODEL_NAME = ', "def main")
                  .replace("print(f\"Catálogo codificado", "print(f\"Catálogo codificado")))
cells.append(code("""\
model = get_model()
emb = catalog_embeddings(model, catalogo["doc"].tolist())   # cache: rápido após a 1ª vez

rankers_deep = {
    "deep_dense":  make_dense_ranker(model, catalogo, emb),
    "deep_hybrid": make_hybrid_ranker(model, catalogo, emb),
}
for nome, rk in rankers_deep.items():
    m, det_val[nome], _ = evaluate_ranker(rk, val)
    print(f"{nome:<11} {fmt(m)}")"""))
cells.append(md("""**Ablação crucial (validação):** codificando o texto **cru** (sem o
pré-processamento da Seção 2), a abordagem neural despenca para P@1 = 0,520 (densa) e
0,588 (híbrida) — queda de ~40 p.p. O modelo semântico não conhece o jargão de pedidos
(`C/6`, `CERV`, `12X350ML`); a normalização é crítica para as duas abordagens.
(Reprodução: `python src/approach2_deep.py --split val --raw-text`.)

**Variante selecionada: híbrida** (melhor R@5 na validação e menor custo por query)."""))

# ---------------------------------------------------------------- teste
cells.append(md("""## 6. Avaliação final no conjunto de teste

`queries_test.csv` é usado **uma única vez**, aqui, para as métricas definitivas — nenhuma
decisão de desenvolvimento foi tomada com ele."""))
cells.append(code("""\
todos = {**rankers_classicos, **rankers_deep}
linhas, det_test = [], {}
for nome, rk in todos.items():
    m, det_test[nome], _ = evaluate_ranker(rk, test)
    linhas.append({"variante": nome, **{k: round(v, 3) for k, v in m.items() if k != "n"}})
pd.DataFrame(linhas).set_index("variante")"""))
cells.append(code("""\
# Tabela comparativa do enunciado (variantes selecionadas na validação)
comp = pd.DataFrame([
    {"Abordagem": "TF-IDF char (clássica)", **{k: round(v,3) for k,v in
        compute_metrics([[p for p,_ in d['top']] for d in det_test['tfidf_char']],
                        test['matched_id'].tolist()).items() if k!='n'},
     "Custo": "Gratuito (CPU)", "Complexidade": "Baixa"},
    {"Abordagem": "BM25 própria (clássica)", **{k: round(v,3) for k,v in
        compute_metrics([[p for p,_ in d['top']] for d in det_test['bm25']],
                        test['matched_id'].tolist()).items() if k!='n'},
     "Custo": "Gratuito (CPU)", "Complexidade": "Baixa"},
    {"Abordagem": "Híbrida BM25+NN (deep)", **{k: round(v,3) for k,v in
        compute_metrics([[p for p,_ in d['top']] for d in det_test['deep_hybrid']],
                        test['matched_id'].tolist()).items() if k!='n'},
     "Custo": "Gratuito (local; modelo 470 MB)", "Complexidade": "Média"},
]).set_index("Abordagem")
comp"""))

# ---------------------------------------------------------------- qualitativa
cells.append(md("""## 7. Análise qualitativa

### 7.1 Acertos, erros e comparação direta (teste)"""))
cells.append(code("""\
def tabela_erros(details, nome):
    hits = [d for d in details if d["top"] and d["top"][0][0] == d["gold"]]
    errs = [d for d in details if not d["top"] or d["top"][0][0] != d["gold"]]
    print(f"{nome}: {len(hits)} acertos, {len(errs)} erros (P@1={len(hits)/len(details):.3f})")
    rows = []
    for d in errs:
        ids5 = [p for p, _ in d["top"]]
        rows.append({"query": d["text"],
                     "esperado": id2name.get(d["gold"], "?"),
                     "obtido (top-1)": id2name.get(ids5[0], "—"),
                     "pos. do correto": ids5.index(d["gold"]) + 1 if d["gold"] in ids5 else ">5"})
    return pd.DataFrame(rows), {d["text"] for d in errs}

df_err_c, errs_c = tabela_erros(det_test["tfidf_char"], "Abordagem 1 (tfidf_char)")
display(df_err_c)
df_err_d, errs_d = tabela_erros(det_test["deep_hybrid"], "Abordagem 2 (deep_hybrid)")
display(df_err_d)
print(f"Só o clássico errou (deep acertou): {len(errs_c - errs_d)}")
print(f"Só o deep errou (clássico acertou): {len(errs_d - errs_c)}")
print(f"Erros em comum: {len(errs_c & errs_d)}")"""))
cells.append(md("""**Leitura dos erros.** Os 2 erros do clássico são casos-limite: a fralda
*128 unidades* (nosso pré-processamento remove "\\<n\\> unidades" como multiplicidade de
embalagem — mas em fraldas a contagem é o tamanho do produto) e o espumante *brut* sem cor
especificada (rosé × branco — genuinamente ambíguo). Os erros do deep concentram-se em
**variante/sabor errado** (maracujá→manga Tang), **tamanho/marca** (Salsicha Ceratti→
Perdigão) e **categoria arrastada pela semântica** (pipoca de microondas→saco para
microondas).

### 7.2 Casos ambíguos (top-2 com scores quase empatados)"""))
cells.append(code("""\
rows = []
for d in det_test["tfidf_char"]:
    if len(d["top"]) >= 2 and d["top"][0][1] - d["top"][1][1] < 0.01:
        rows.append({"query": d["text"],
                     "top-1": id2name.get(d["top"][0][0], "?"),
                     "top-2": id2name.get(d["top"][1][0], "?"),
                     "Δ score": round(d["top"][0][1] - d["top"][1][1], 4)})
pd.DataFrame(rows)"""))
cells.append(md("""Os empates são versões **unitária × multipack** ("…lata 350ml" ×
"…lata 350ml 12 un") e variantes não especificadas na query. Com o desempate determinístico
pela ordem do catálogo, a versão unitária (que aparece primeiro) é preferida.

### 7.3 Casos NO_MATCH

Queries reais de `queries.csv` cujas marcas **não existem** no catálogo. Nenhuma abordagem
tem rejeição nativa — sempre devolvem algo; a defesa é um **limiar sobre o score**."""))
cells.append(code("""\
NO_MATCH_QUERIES = [
    "MORMAII LATA BRANCO C/6",
    "Limpador para Casa Perfumado QUALITÁ Lavanda 2 litros",
    "Farinha de Chia Taeq Pouch 150g",
    "Rabo de Bovino Congelado SWIFT 2Kg",
    "CHICLETE BUZZY ROSA MORANGO",
]
CONTROLE = ["Café Solúvel Granulado Forte Nescafé Tradição Sachê 40g",
            "FANTA LARANJA 2L C/6"]

rows = []
for grupo, qs in [("NO_MATCH", NO_MATCH_QUERIES), ("controle (existe)", CONTROLE)]:
    for q in qs:
        for nome in ("tfidf_char", "deep_hybrid"):
            pid, sc = todos[nome](q)[0]
            rows.append({"grupo": grupo, "query": q, "abordagem": nome,
                         "top-1": id2name.get(pid, "?"), "score": round(sc, 3)})
pd.DataFrame(rows)"""))
cells.append(md("""**Conclusões sobre NO_MATCH:** no TF-IDF-char os scores de NO_MATCH ficam
em 0,24–0,68, bem abaixo dos matches corretos descritivos (p5 = 0,880 na validação) — um
limiar funciona. Na neural, os scores continuam altos mesmo sem o produto existir (até 0,90
para o limpador Qualitá), pois sempre há substituto semanticamente próximo — limiar pouco
confiável. **O limiar depende do estilo da query**: no estilo abreviado de `queries.csv`, um
match correto pode pontuar ~0,73 ("FANTA LARANJA 2L C/6") e NO_MATCHes ficam em ~0,41–0,43;
≈0,55 separa razoavelmente os regimes nesse estilo."""))

# ---------------------------------------------------------------- fill
cells.append(md("""## 8. Preenchimento de `queries.csv`

A descrição dos dados diz que `matched_id` é "a ser preenchido pelo grupo". Aplicamos a
variante vencedora (TF-IDF-char) em lote às 16.441 queries, gravando também o `score` do
top-1 para permitir o filtro de possíveis NO_MATCH. O arquivo original em `Dados/` **não é
modificado**."""))
cells.append(code("""\
vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
doc_matrix = l2_normalize(vec.fit_transform(catalogo["doc"]))
ids_arr = np.array(catalogo["product_id"])

t0 = time.perf_counter()
q_norm = [normalize(t) for t in queries["text"]]
matched, scores = [], []
for ini in range(0, len(queries), 2000):
    q_m = l2_normalize(vec.transform(q_norm[ini:ini + 2000]))
    sims = (q_m @ doc_matrix.T).toarray()
    best = sims.argmax(axis=1)
    matched.extend(ids_arr[best])
    scores.extend(sims[np.arange(len(best)), best])

preenchido = pd.DataFrame({"text": queries["text"], "matched_id": matched,
                           "score": np.round(scores, 4)})
preenchido.to_csv(RESULTS / "queries_preenchido.csv", index=False, encoding="utf-8")
print(f"{len(preenchido)} queries preenchidas em {time.perf_counter()-t0:.1f}s")
for limiar in (0.45, 0.55, 0.65):
    n = (preenchido['score'] < limiar).sum()
    print(f"score < {limiar:.2f} (possível NO_MATCH): {n} ({n/len(preenchido):.1%})")
preenchido.head(8)"""))

# ---------------------------------------------------------------- conclusões
cells.append(md("""## 9. Conclusões

| Abordagem (teste, 250 q) | P@1 | MRR@5 | R@5 | Tempo | Custo | Complexidade |
|---|---|---|---|---|---|---|
| **TF-IDF caracteres** | **0,992** | **0,996** | **1,000** | ~12 s | Gratuito | Baixa |
| BM25 (própria) | 0,988 | 0,992 | 1,000 | ~0,2 s | Gratuito | Baixa |
| Híbrida BM25 + MiniLM | 0,944 | 0,962 | 0,984 | ~7 s (+106 s de indexação única) | Gratuito (local) | Média |

1. **Em catálogo de vocabulário controlado, o clássico bem pré-processado vence**: TF-IDF-char
   0,992 e BM25 0,988 (a ~1 ms/query) contra 0,944 da neural.
2. **O pré-processamento domina o resultado**: sem ele a neural perde ~40 p.p. de P@1 —
   é a tradução do jargão (`C/6`, `CERV`) para o vocabulário do catálogo que resolve a tarefa.
3. **Os erros restantes são de granularidade**, não de entendimento: multipack, sabor, cor,
   contagem — pedem extração estruturada de atributos, não modelos maiores.
4. **Melhorias futuras**: fine-tuning do bi-encoder (triplet loss com pares minerados de
   `queries.csv`), re-rank com cross-encoder ou LLM (zero/few-shot nos top-10 do BM25),
   limiar de NO_MATCH calibrado por estilo de query, fusão de scores BM25+embedding."""))

nb = nbf.v4.new_notebook(cells=cells, metadata={
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"},
})
out = ROOT / "T2_Matching_Produtos.ipynb"
nbf.write(nb, str(out))
print(f"Notebook gerado: {out} ({len(cells)} células)")
