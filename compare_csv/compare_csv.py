#!/usr/bin/env python3
"""
compare_csv.py
Сравнить два CSV и вывести записи, присутствующие в обоих.
Выход: CSV с колонками = пересечение колонок (порядок — как в большем файле),
с обязательным включением 'Position' из большего файла (если он там есть).
Matching priority: URL -> Name+Year -> Name.
"""

import csv
import argparse
import sys

def norm(s):
    return (s or '').strip().lower()

def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []
    return headers, rows

def build_norm_map(headers):
    # map normalized_name -> original_header_name
    return { norm(h): h for h in headers }

def make_key(row, key_fields):
    parts = [ norm(row.get(f, '')) for f in key_fields ]
    return "||".join(parts)

def build_map(rows, key_fields):
    m = {}
    for row in rows:
        k = make_key(row, key_fields)
        if not k:
            continue
        if k in m:
            # keep list if duplicates
            if isinstance(m[k], list):
                m[k].append(row)
            else:
                m[k] = [m[k], row]
        else:
            m[k] = row
    return m

def parse_position(value):
    try:
        return int(value)
    except Exception:
        return 10**9  # большие числа отправляем в конец

def main(file1, file2, output_path=None):
    h1, r1 = read_csv(file1)
    h2, r2 = read_csv(file2)

    norm1 = build_norm_map(h1)
    norm2 = build_norm_map(h2)

    common_norm = set(norm1) & set(norm2)

    # choose matching key
    if 'url' in common_norm:
        key_norm = ['url']
    elif 'name' in common_norm and 'year' in common_norm:
        key_norm = ['name', 'year']
    elif 'name' in common_norm:
        key_norm = ['name']
    else:
        print("Ошибка: нет общих полей для сопоставления (нет url, name+year или name).", file=sys.stderr)
        sys.exit(2)

    key_fields1 = [ norm1[k] for k in key_norm ]
    key_fields2 = [ norm2[k] for k in key_norm ]

    map1 = build_map(r1, key_fields1)
    map2 = build_map(r2, key_fields2)

    # определяем "больший" файл по числу строк
    if len(r1) >= len(r2):
        larger_headers, larger_rows, larger_map, larger_norm_map, larger_path = h1, r1, map1, norm1, file1
        smaller_headers, smaller_rows, smaller_map, smaller_norm_map, smaller_path = h2, r2, map2, norm2, file2
    else:
        larger_headers, larger_rows, larger_map, larger_norm_map, larger_path = h2, r2, map2, norm2, file2
        smaller_headers, smaller_rows, smaller_map, smaller_norm_map, smaller_path = h1, r1, map1, norm1, file1

    # формируем список колонок для вывода:
    # порядок — как в большем файле; только колонки, которые есть в обоих; Position из большого файла — в начале (если есть)
    out_cols = []
    if 'position' in larger_norm_map:
        out_cols.append(larger_norm_map['position'])
    for col in larger_headers:
        if norm(col) == 'position':
            continue
        if norm(col) in (set(larger_norm_map) & set(smaller_norm_map)):
            out_cols.append(col)
    # уникализируем и оставляем порядок
    seen = set(); final_cols = []
    for c in out_cols:
        if c not in seen:
            final_cols.append(c); seen.add(c)

    if not final_cols:
        print("Ошибка: нет общих колонок для вывода.", file=sys.stderr)
        sys.exit(3)

    fout = open(output_path, 'w', newline='', encoding='utf-8') if output_path else sys.stdout
    writer = csv.DictWriter(fout, fieldnames=final_cols)
    writer.writeheader()

    intersection = set(larger_map.keys()) & set(smaller_map.keys())

    results = []
    for k in sorted(intersection):
        lrows = larger_map[k] if isinstance(larger_map[k], list) else [larger_map[k]]
        srows = smaller_map[k] if isinstance(smaller_map[k], list) else [smaller_map[k]]
        for lrow in lrows:
            srow = srows[0]  # при необходимости брать первый из меньшего
            out_row = {}
            for col in final_cols:
                v = (lrow.get(col, '') or '').strip()
                if v == '':
                    # fallback: найти соответствующее имя колонки в маленьком файле по норм. имени
                    nn = norm(col)
                    small_col = smaller_norm_map.get(nn)
                    if small_col:
                        v = (srow.get(small_col, '') or '').strip()
                out_row[col] = v
            results.append(out_row)

    # сортировка по Position
    if 'position' in [norm(c) for c in final_cols]:
        pos_col = [c for c in final_cols if norm(c) == 'position'][0]
        results.sort(key=lambda r: parse_position(r.get(pos_col, '')))

    for row in results:
        writer.writerow(row)

    if output_path:
        fout.close()
    print(f"Готово. Совпадающих записей: {len(intersection)}. Вывод: {output_path or 'stdout'}", file=sys.stderr)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Сравнить два CSV и вывести записи, присутствующие в обоих. Output содержит общие столбцы и Position из большего файла.')
    parser.add_argument('file1', help='Первый CSV')
    parser.add_argument('file2', help='Второй CSV')
    parser.add_argument('-o','--output', help='Файл для вывода (по умолчанию stdout)')
    args = parser.parse_args()
    main(args.file1, args.file2, args.output)
