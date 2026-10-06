import csv

input_file = "artist_counts_uts.csv"
output_file = "artists_line_uts.txt"

artists = []

with open(input_file, "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        artist = row["artist"].strip()
        if artist:
            artists.append(artist)

result = ",".join(artists)

with open(output_file, "w", encoding="utf-8") as f:
    f.write(result)

print(f"Готово. Сохранено в {output_file}")