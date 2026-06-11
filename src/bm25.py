# -*- coding: utf-8 -*-
"""
Implementação própria do BM25 (Okapi BM25) com índice invertido.

score(q, d) = soma_{t em q} IDF(t) * f(t,d)*(k1+1) / (f(t,d) + k1*(1 - b + b*|d|/avgdl))
IDF(t) = ln( (N - df(t) + 0.5) / (df(t) + 0.5) + 1 )
"""
import math
from collections import Counter, defaultdict

import numpy as np


class BM25:
    def __init__(self, tokenized_docs, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.N = len(tokenized_docs)
        self.doc_len = np.array([len(d) for d in tokenized_docs], dtype=np.float64)
        self.avgdl = self.doc_len.mean() if self.N else 0.0

        # índice invertido: termo -> [(doc_id, freq), ...]
        self.index = defaultdict(list)
        for doc_id, doc in enumerate(tokenized_docs):
            for term, freq in Counter(doc).items():
                self.index[term].append((doc_id, freq))

        self.idf = {
            term: math.log((self.N - len(posts) + 0.5) / (len(posts) + 0.5) + 1.0)
            for term, posts in self.index.items()
        }

    def scores(self, query_tokens):
        """Vetor de scores BM25 da query contra todos os documentos."""
        s = np.zeros(self.N)
        norm = self.k1 * (1.0 - self.b + self.b * self.doc_len / self.avgdl)
        for term in query_tokens:
            posts = self.index.get(term)
            if not posts:
                continue
            idf = self.idf[term]
            for doc_id, freq in posts:
                s[doc_id] += idf * freq * (self.k1 + 1.0) / (freq + norm[doc_id])
        return s

    def topk(self, query_tokens, k=5):
        s = self.scores(query_tokens)
        # ordenação estável: empates resolvidos pela ordem do catálogo (determinístico)
        top = np.argsort(-s, kind="stable")[:k]
        return [(int(i), float(s[i])) for i in top]
