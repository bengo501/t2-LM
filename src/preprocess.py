# -*- coding: utf-8 -*-
"""
Etapa 1.1 — Pré-processamento textual.

Normaliza tanto as queries quanto os nomes de produto do catálogo:
  - minúsculas e remoção de acentos;
  - expansão de "s/" -> "sem" e "c/" -> "com" (quando seguidos de palavra);
  - remoção de quantidades de embalagem (C/6, C/12, CX, FD, 12X350ML -> 350ml, UND...);
  - normalização de unidades de medida (2L -> 2l, 350 ML -> 350ml, 15 GR -> 15g);
  - normalização de abreviações comuns do varejo (cerv -> cerveja, refrig -> refrigerante...);
  - remoção de pontuação e stopwords do português.

Observação metodológica: NÃO removemos a palavra "sem" como stopword, pois ela é
discriminativa em produtos ("sem açúcar", "sem gás", "sem lactose"). "com" é
removida porque a ausência dela não gera confusão ("água gás" ≠ "água sem gás").
"""
import re
import unicodedata

# stopwords do português relevantes para descrições de produto
STOPWORDS = {
    "de", "do", "da", "dos", "das", "e", "o", "a", "os", "as",
    "um", "uma", "para", "por", "em", "no", "na", "nos", "nas", "ao", "com",
}

# abreviações comuns em pedidos de compra -> forma do catálogo.
# Mantemos apenas abreviações NÃO ambíguas: "cond" (condensado x condicionador)
# e "sab" (sabão x sabonete), por exemplo, ficaram de fora de propósito.
ABBREVIATIONS = {
    "cerv": "cerveja",
    "refri": "refrigerante",
    "refrig": "refrigerante",
    "choc": "chocolate",
    "achoc": "achocolatado",
    "bisc": "biscoito",
    "marg": "margarina",
    "maion": "maionese",
    "shamp": "shampoo",
    "energ": "energetico",
    "grf": "garrafa",
    "lt": "lata",
}

# unidades de medida -> forma canônica (sem espaço, sufixo padronizado)
_UNIT_MAP = {
    "l": "l", "lt": "l", "lts": "l", "litro": "l", "litros": "l", "ltr": "l",
    "ml": "ml", "mls": "ml",
    "g": "g", "gr": "g", "grs": "g", "grama": "g", "gramas": "g",
    "kg": "kg", "kgs": "kg", "quilo": "kg", "kilo": "kg",
    "mg": "mg",
    "un": "", "und": "", "unid": "", "unidade": "", "unidades": "", "u": "",
}

_PACK_WORDS = {"cx", "fd", "pct", "dz", "fardo", "caixa"}  # multiplicidade de embalagem


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def normalize(text: str) -> str:
    """Normaliza um texto (query ou nome de produto) para o matching."""
    t = strip_accents(str(text).lower())

    # s/acucar -> sem acucar ; c/ gas -> com gas  (antes de remover pontuação)
    t = re.sub(r"\bs/\s*(?=[a-z])", "sem ", t)
    t = re.sub(r"\bc/\s*(?=[a-z])", "com ", t)

    # quantidades de embalagem: c/6, c-12, 12x350ml (mantém o tamanho unitário)
    t = re.sub(r"\bc[/\-]?\d+\b", " ", t)                       # c/6, c12
    t = re.sub(r"\b\d+\s*x\s*(\d+)", r" \1", t)                 # 12x350ml -> 350ml
    t = re.sub(r"\b(cx|fd|pct|dz)\s*\d+\b", " ", t)             # cx12, fd6

    # separa número de unidade colada (350ml -> 350 ml) para canonizar depois
    t = re.sub(r"(\d+)[\.,](\d+)", r"\1.\2", t)                 # 1,5l -> 1.5l
    t = re.sub(r"(\d+(?:\.\d+)?)\s*([a-z]+)", r"\1 \2", t)

    # pontuação -> espaço
    t = re.sub(r"[^a-z0-9.\s]", " ", t)

    tokens = []
    parts = t.split()
    i = 0
    while i < len(parts):
        tok = parts[i]
        # número seguido de unidade -> token canônico colado (2 l -> 2l)
        if re.fullmatch(r"\d+(?:\.\d+)?", tok) and i + 1 < len(parts):
            unit = _UNIT_MAP.get(parts[i + 1])
            if unit is not None:
                num = tok.rstrip("0").rstrip(".") if "." in tok else tok
                if unit:                      # 2 litros -> 2l ; 350 ml -> 350ml
                    tokens.append(num + unit)
                # unidade de contagem (6 und) -> descarta número e unidade
                i += 2
                continue
        if tok in _PACK_WORDS or _UNIT_MAP.get(tok) == "":
            i += 1
            continue
        tok = ABBREVIATIONS.get(tok, tok)
        if tok and tok not in STOPWORDS:
            tokens.append(tok)
        i += 1
    return " ".join(tokens)


def tokenize(text: str) -> list:
    """Normaliza e devolve a lista de tokens (para o BM25)."""
    return normalize(text).split()


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    exemplos = [
        "COCA COLA 1L C/6",
        "SKOL LATA 350ml C/12",
        "FANTA LARANJA 2L C/6",
        "MONSTER BRANCO S/ACUCAR C/6 UNID",
        "FINI MINI BANANAS 12X15 GR Und",
        "Refrigerante guaraná antarctica 200ml",
        "Suco de uva orgânico aliança 1 litro",
        "CERV HEINEKEN LONG NECK 330ML CX24",
        "Água mineral sem gás prata 300ml",
        "LEITE COND ITALAC 395G",
        "1,5L AGUA C/ GAS",
    ]
    for e in exemplos:
        print(f"{e!r:55} -> {normalize(e)!r}")
