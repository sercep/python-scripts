import csv
from collections import Counter

input_file = "input.csv"
output_file = "artist_counts_uts.csv"

uts_threshold = 1680000000  # считать только строки, где uts > этого числа

artist_counter = Counter()

with open(input_file, "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        try:
            uts = int(row["uts"].strip())
        except (ValueError, KeyError):
            continue  # пропускаем битые или пустые строки

        if uts > uts_threshold:
            artist = row["artist"].strip()
            if artist:
                artist_counter[artist] += 1

# сортировка по убыванию количества
sorted_artists = artist_counter.most_common()

with open(output_file, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["artist", "count"])
    writer.writerows(sorted_artists)

print(f"Готово. Результат сохранён в {output_file}")