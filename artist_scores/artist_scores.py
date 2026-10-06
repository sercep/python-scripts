#!/usr/bin/env python3
"""
Скрипт подсчёта воспроизведений по исполнителям с суммированием баллов
по нескольким временным периодам.

Использование:
    python artist_scores.py <путь_к_csv> [--top N] [--output результат.csv]

Аргументы:
    путь_к_csv   -- путь к CSV-файлу с историей прослушиваний
    --top N      -- вывести только топ-N исполнителей (по умолчанию: все)
    --output     -- сохранить результат в файл; если расширение .csv -- сохраняет
                    в CSV-формате, иначе -- в текстовом виде (по умолчанию: консоль)
"""

import csv
import sys
import argparse
from datetime import datetime, timezone
from collections import defaultdict


# ──────────────────────────────────────────────────────────────────────────────
# Временные периоды: (название, начало, множитель)
# ──────────────────────────────────────────────────────────────────────────────

PERIODS = [
    ("Всё время",     datetime.min.replace(tzinfo=timezone.utc), 1),
    ("с 1 янв 2017",  datetime(2017,  1,  1, tzinfo=timezone.utc), 2),
    ("с 1 янв 2019",  datetime(2019,  1,  1, tzinfo=timezone.utc), 3),
    ("с 1 янв 2020",  datetime(2020,  1,  1, tzinfo=timezone.utc), 4),
    ("с 1 янв 2021",  datetime(2021,  1,  1, tzinfo=timezone.utc), 4),
    ("с 1 янв 2022",  datetime(2022,  1,  1, tzinfo=timezone.utc), 4),
    ("с 1 янв 2023",  datetime(2023,  1,  1, tzinfo=timezone.utc), 4),
    ("с 1 янв 2024",  datetime(2024,  1,  1, tzinfo=timezone.utc), 4),
    ("с 1 янв 2025",  datetime(2025,  1,  1, tzinfo=timezone.utc), 5),
    ("с 9 мая 2025",  datetime(2025,  5,  9, tzinfo=timezone.utc), 6),
    ("с 10 сен 2025", datetime(2025,  9, 10, tzinfo=timezone.utc), 10),
    ("с 1 янв 2026",  datetime(2026,  1,  1, tzinfo=timezone.utc), 12),
]

PERIOD_NAMES       = [p[0] for p in PERIODS]
PERIOD_MULTIPLIERS = [p[2] for p in PERIODS]


# ──────────────────────────────────────────────────────────────────────────────
# Парсинг
# ──────────────────────────────────────────────────────────────────────────────

def parse_timestamp(uts_str: str) -> datetime | None:
    """Преобразует Unix-timestamp (строка) в datetime с UTC."""
    try:
        return datetime.fromtimestamp(int(uts_str), tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None


def load_csv(path: str):
    """
    Читает CSV и возвращает список кортежей (artist, dt).
    Пропускает строки с отсутствующим или невалидным timestamp.
    """
    records = []
    skipped = 0
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            dt = parse_timestamp(row.get("uts", ""))
            artist = (row.get("artist") or "").strip()
            if dt is None or not artist:
                skipped += 1
                continue
            records.append((artist, dt))
    if skipped:
        print(f"[!] Пропущено строк (нет даты / исполнителя): {skipped}", file=sys.stderr)
    return records


# ──────────────────────────────────────────────────────────────────────────────
# Подсчёт
# ──────────────────────────────────────────────────────────────────────────────

def count_plays(records):
    """
    Возвращает словарь:
        artist -> list[int]  (кол-во воспроизведений в каждом периоде)
    """
    counts: dict[str, list[int]] = defaultdict(lambda: [0] * len(PERIODS))
    for artist, dt in records:
        for i, (_, since, _mult) in enumerate(PERIODS):
            if dt >= since:
                counts[artist][i] += 1
    return counts


def compute_scores(counts: dict):
    """
    Суммирует воспроизведения по всем периодам с учётом множителей ->
    итоговый балл. Возвращает список (artist, total_score, [per-period counts]).
    """
    result = []
    for artist, period_counts in counts.items():
        total = sum(cnt * mult for cnt, mult in zip(period_counts, PERIOD_MULTIPLIERS))
        result.append((artist, total, period_counts))
    result.sort(key=lambda x: (-x[1], x[0].lower()))
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Форматирование вывода — текст
# ──────────────────────────────────────────────────────────────────────────────

def format_report(scored: list, top_n: int | None = None) -> str:
    if top_n:
        scored = scored[:top_n]

    max_name = max((len(a) for a, *_ in scored), default=20)
    max_name = max(max_name, 12)
    col_w = 7

    # Заголовок: показываем множитель там, где он > 1
    def period_header(name, mult):
        return f"{name} (x{mult})" if mult > 1 else name

    headers = [period_header(n, m) for n, m in zip(PERIOD_NAMES, PERIOD_MULTIPLIERS)]
    col_w2 = max(col_w, max(len(h) for h in headers))

    header_parts = [f"{'Исполнитель':<{max_name}}", f"{'Балл':>{col_w}}"]
    for h in headers:
        header_parts.append(f"{h:>{col_w2}}")
    header = "  ".join(header_parts)
    sep = "─" * len(header)

    lines = [sep, header, sep]
    for rank, (artist, total, period_counts) in enumerate(scored, 1):
        row_parts = [f"{artist:<{max_name}}", f"{total:>{col_w}}"]
        for cnt in period_counts:
            row_parts.append(f"{cnt:>{col_w2}}")
        lines.append(f"{rank:>4}. {'  '.join(row_parts)}")

    lines.append(sep)
    lines.append(f"Всего уникальных исполнителей: {len(scored)}")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Форматирование вывода — CSV
# ──────────────────────────────────────────────────────────────────────────────

def write_csv(path: str, scored: list, top_n: int | None = None) -> None:
    """Сохраняет результат в CSV-файл."""
    if top_n:
        scored = scored[:top_n]

    # Колонки с множителем помечаем в заголовке
    def col_name(name, mult):
        return f"{name} (x{mult})" if mult > 1 else name

    col_names = [col_name(n, m) for n, m in zip(PERIOD_NAMES, PERIOD_MULTIPLIERS)]
    fieldnames = ["rank", "artist", "score"] + col_names

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for rank, (artist, total, period_counts) in enumerate(scored, 1):
            row = {"rank": rank, "artist": artist, "score": total}
            for cname, cnt in zip(col_names, period_counts):
                row[cname] = cnt
            writer.writerow(row)


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Подсчёт воспроизведений и баллов по исполнителям"
    )
    parser.add_argument("csv_file", help="Путь к CSV-файлу с историей прослушиваний")
    parser.add_argument(
        "--top", type=int, default=None, metavar="N",
        help="Показать только топ-N исполнителей"
    )
    parser.add_argument(
        "--output", default=None, metavar="FILE",
        help="Сохранить результат в файл (.csv -> CSV-формат, иначе текст)"
    )
    args = parser.parse_args()

    print(f"Загрузка данных из '{args.csv_file}'...", file=sys.stderr)
    records = load_csv(args.csv_file)
    print(f"Загружено записей: {len(records)}", file=sys.stderr)

    counts = count_plays(records)
    scored = compute_scores(counts)

    if args.output:
        if args.output.lower().endswith(".csv"):
            write_csv(args.output, scored, top_n=args.top)
        else:
            report = format_report(scored, top_n=args.top)
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(report + "\n")
        print(f"Результат сохранён в '{args.output}'", file=sys.stderr)
    else:
        print(format_report(scored, top_n=args.top))


if __name__ == "__main__":
    main()