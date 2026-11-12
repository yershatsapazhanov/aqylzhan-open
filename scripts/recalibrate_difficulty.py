#!/usr/bin/env python3
"""Пересчёт сложности задач по реальным ответам учеников.

Правила (см. docs/methodology.md):
  1. Пропущенные ответы (skipped=true) НЕ считаются ошибками и исключаются.
  2. Задача рассматривается, только если непропущенных попыток n > 10.
  3. Отклонение должно быть значимым: двусторонний точный биномиальный тест, p < 0.05.
  4. Новая оценка считается с байесовским сглаживанием:
         p_new = (k * p_old + успехи) / (k + n),  k = сила априори (по умолчанию 10).

Вход (CSV): question_id, expected_p, correct, skipped
  expected_p — ожидаемая доля верных ответов по текущей сложности (0..1)
  correct, skipped — 1/0 или true/false

Запуск:
  python recalibrate_difficulty.py attempts.csv
  python recalibrate_difficulty.py --demo
"""
import argparse
import csv
import random
import sys
from collections import defaultdict
from math import comb

MIN_ATTEMPTS = 10      # нужно строго больше
ALPHA = 0.05
PRIOR_STRENGTH = 10


def binom_two_sided_p(k: int, n: int, p0: float) -> float:
    """Точный двусторонний биномиальный тест (метод малых вероятностей)."""
    if p0 <= 0 or p0 >= 1:
        return 1.0
    pmf = [comb(n, i) * p0 ** i * (1 - p0) ** (n - i) for i in range(n + 1)]
    observed = pmf[k]
    eps = 1e-12
    return min(1.0, sum(x for x in pmf if x <= observed * (1 + eps)))


def truthy(v) -> bool:
    return str(v).strip().lower() in {"1", "true", "t", "yes", "y"}


def recalibrate(rows):
    stats = defaultdict(lambda: {"p0": None, "n": 0, "k": 0, "skipped": 0})
    for r in rows:
        s = stats[r["question_id"]]
        s["p0"] = float(r["expected_p"])
        if truthy(r["skipped"]):
            s["skipped"] += 1
            continue
        s["n"] += 1
        s["k"] += 1 if truthy(r["correct"]) else 0

    result = []
    for qid, s in stats.items():
        n, k, p0 = s["n"], s["k"], s["p0"]
        if n <= MIN_ATTEMPTS:
            result.append((qid, p0, n, k, None, None, "мало данных"))
            continue
        pval = binom_two_sided_p(k, n, p0)
        if pval < ALPHA:
            p_new = (PRIOR_STRENGTH * p0 + k) / (PRIOR_STRENGTH + n)
            result.append((qid, p0, n, k, pval, p_new, "ПЕРЕСЧИТАТЬ"))
        else:
            result.append((qid, p0, n, k, pval, None, "ок"))
    return result


def demo_rows():
    rng = random.Random(42)
    # (id, ожидаемая доля верных, реальная доля верных, число попыток)
    spec = [("q1", 0.70, 0.70, 60), ("q2", 0.70, 0.35, 60),
            ("q3", 0.50, 0.52, 40), ("q4", 0.40, 0.75, 30),
            ("q5", 0.60, 0.20, 8)]
    rows = []
    for qid, p0, true_p, n in spec:
        for _ in range(n):
            rows.append({"question_id": qid, "expected_p": p0,
                         "correct": rng.random() < true_p, "skipped": False})
        for _ in range(5):  # пропуски не должны влиять
            rows.append({"question_id": qid, "expected_p": p0,
                         "correct": False, "skipped": True})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--demo", action="store_true", help="синтетические данные")
    a = ap.parse_args()
    if a.demo:
        rows = demo_rows()
    elif a.csv:
        with open(a.csv, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    else:
        ap.error("укажите CSV или --demo")

    print(f"{'id':<6}{'было':>6}{'n':>5}{'верно':>7}{'p-value':>10}{'стало':>8}  решение")
    for qid, p0, n, k, pv, pn, note in sorted(recalibrate(rows)):
        pv_s = f"{pv:.4f}" if pv is not None else "-"
        pn_s = f"{pn:.2f}" if pn is not None else "-"
        print(f"{qid:<6}{p0:>6.2f}{n:>5}{k:>7}{pv_s:>10}{pn_s:>8}  {note}")


if __name__ == "__main__":
    sys.exit(main())
