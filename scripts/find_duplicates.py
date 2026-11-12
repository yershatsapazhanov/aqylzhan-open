#!/usr/bin/env python3
"""Поиск дублей в банке задач.

Два уровня:
  1. Точные дубли: совпадение текста после нормализации
     (нижний регистр, без знаков препинания, один пробел).
  2. Перефразированные дубли: одинаковый числовой «отпечаток» —
     отсортированный набор всех чисел из условия.
     Отпечаток даёт кандидатов, а не приговор: решает человек.

Вход (CSV): id, text
Запуск:
  python find_duplicates.py questions.csv
  python find_duplicates.py --demo
"""
import argparse
import csv
import re
import sys
from collections import defaultdict

NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")


def normalize(text: str) -> str:
    t = text.lower()
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    return re.sub(r"\s+", " ", t).strip()


def fingerprint(text: str):
    nums = [n.replace(",", ".") for n in NUM_RE.findall(text)]
    return tuple(sorted(nums, key=float)) if nums else None


def find(rows):
    exact, fp = defaultdict(list), defaultdict(list)
    for r in rows:
        exact[normalize(r["text"])].append(r["id"])
        f = fingerprint(r["text"])
        if f:
            fp[f].append(r["id"])
    exact_groups = [ids for ids in exact.values() if len(ids) > 1]
    in_exact = {i for g in exact_groups for i in g}
    fp_groups = []
    for ids in fp.values():
        if len(ids) < 2:
            continue
        # не повторять то, что уже найдено как точный дубль
        if set(ids) <= in_exact and any(set(ids) <= set(g) for g in exact_groups):
            continue
        fp_groups.append(ids)
    return exact_groups, fp_groups


DEMO = [
    {"id": "a1", "text": "Найдите 25% от числа 80."},
    {"id": "a2", "text": "найдите 25% от числа 80"},
    {"id": "a3", "text": "Чему равны 25 процентов от 80?"},
    {"id": "a4", "text": "У Айдара было 12 яблок, он отдал 5. Сколько осталось?"},
    {"id": "a5", "text": "Сколько осталось у Айдара, если из 12 яблок он отдал 5?"},
    {"id": "a6", "text": "Периметр квадрата равен 36 см. Найдите сторону."},
]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        rows = DEMO
    elif a.csv:
        with open(a.csv, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    else:
        ap.error("укажите CSV или --demo")

    exact, fp = find(rows)
    print("Точные дубли:")
    for g in exact:
        print("  ", ", ".join(g))
    if not exact:
        print("   нет")
    print("Кандидаты в перефразированные дубли (проверить вручную):")
    for g in fp:
        print("  ", ", ".join(g))
    if not fp:
        print("   нет")


if __name__ == "__main__":
    sys.exit(main())
