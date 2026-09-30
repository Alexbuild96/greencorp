"""Считает точность оценки ИИ по заполненному eval/pilot_template.csv.

Запуск: python eval/score.py eval/pilot.csv
Строки без sold_price (ещё не продано) в точности не участвуют.
"""
import csv
import statistics
import sys


def _num(v: str) -> float | None:
    v = (v or "").strip()
    return float(v) if v else None


def score(rows: list[dict]) -> dict:
    sold = [r for r in rows if _num(r["sold_price"]) is not None and _num(r["ai_price_fair"]) is not None]
    errs = [abs(_num(r["ai_price_fair"]) - _num(r["sold_price"])) / _num(r["sold_price"]) for r in sold if _num(r["sold_price"])]
    in_range = [
        _num(r["ai_price_low"]) <= _num(r["sold_price"]) <= _num(r["ai_price_high"])
        for r in sold
        if None not in (_num(r["ai_price_low"]), _num(r["ai_price_high"]))
    ]
    days = [_num(r["days_to_sell"]) for r in sold if _num(r["days_to_sell"]) is not None]
    recognised = [r["ai_model_correct"].strip().lower() in ("1", "y", "yes", "да") for r in rows if r["ai_model_correct"].strip()]
    return {
        "items_total": len(rows),
        "items_sold": len(sold),
        "sell_through": round(len(sold) / len(rows), 2) if rows else None,
        "mape_fair_vs_sold": round(statistics.mean(errs), 3) if errs else None,
        "sold_inside_ai_range": round(sum(in_range) / len(in_range), 2) if in_range else None,
        "median_days_to_sell": statistics.median(days) if days else None,
        "model_recognition_rate": round(sum(recognised) / len(recognised), 2) if recognised else None,
    }


if __name__ == "__main__":
    with open(sys.argv[1], newline="", encoding="utf-8") as f:
        for k, v in score(list(csv.DictReader(f))).items():
            print(f"{k}: {v}")
