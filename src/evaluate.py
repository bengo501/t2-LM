# -*- coding: utf-8 -*-
"""
Métricas de avaliação do trabalho: P@1, MRR@5 e R@5.

Cada ranker devolve, para cada query, uma lista ordenada com os top-5
product_id mais similares. As métricas comparam essa lista com o matched_id.
"""
import time

K = 5


def compute_metrics(ranked_ids, gold_ids, k=K):
    """ranked_ids: lista de listas (top-k ids por query); gold_ids: lista de ids corretos."""
    assert len(ranked_ids) == len(gold_ids)
    n = len(gold_ids)
    p1 = 0
    rr_sum = 0.0
    r5 = 0
    for ranked, gold in zip(ranked_ids, gold_ids):
        topk = list(ranked[:k])
        if topk and topk[0] == gold:
            p1 += 1
        if gold in topk:
            r5 += 1
            rr_sum += 1.0 / (topk.index(gold) + 1)
        # se não aparece no top-k, 1/rank = 0
    return {"P@1": p1 / n, "MRR@5": rr_sum / n, "R@5": r5 / n, "n": n}


def evaluate_ranker(rank_fn, queries_df, k=K):
    """Aplica rank_fn(text) -> [(product_id, score), ...] a cada query e mede o tempo.

    Devolve (metrics, details, elapsed_seconds). details guarda o top-k por query
    para a análise qualitativa.
    """
    ranked_all, details = [], []
    t0 = time.perf_counter()
    for _, row in queries_df.iterrows():
        top = rank_fn(row["text"])[:k]
        ranked_all.append([pid for pid, _ in top])
        details.append({"text": row["text"], "gold": row["matched_id"], "top": top})
    elapsed = time.perf_counter() - t0
    metrics = compute_metrics(ranked_all, queries_df["matched_id"].tolist(), k)
    metrics["tempo_s"] = round(elapsed, 2)
    return metrics, details, elapsed


def fmt(metrics):
    return (f"P@1={metrics['P@1']:.3f}  MRR@5={metrics['MRR@5']:.3f}  "
            f"R@5={metrics['R@5']:.3f}  (n={metrics['n']}, {metrics.get('tempo_s', '?')}s)")
