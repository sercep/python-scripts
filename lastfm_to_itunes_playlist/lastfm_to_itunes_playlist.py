import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# =========================
# НАСТРОЙКИ
# =========================

INPUT_CSV = "lastfm_export.csv"      # твой экспорт Last.fm
OUTPUT_TXT = "itunes_import.txt"     # итоговый TXT
ENCODING_IN = "utf-8"
ENCODING_OUT = "utf-16"  # iTunes обычно нормально ест UTF-16 tab-delimited

# Если хочешь использовать альбом в дедупликации — оставь True
USE_ALBUM_IN_KEY = True

# =========================
# ВСПОМОГАТЕЛЬНОЕ
# =========================

def parse_lastfm_time(s: str) -> datetime:
    # Пример: "20 Mar 2026, 14:54"
    return datetime.strptime(s.strip(), "%d %b %Y, %H:%M")

def format_itunes_datetime(dt: datetime) -> str:
    # Формат похожий на экспорт iTunes RU:
    # 20.03.2026 14:54
    return dt.strftime("%d.%m.%Y %H:%M")

def safe_str(x):
    return x.strip() if x else ""

# =========================
# ЧТЕНИЕ И АГРЕГАЦИЯ
# =========================

tracks = {}

with open(INPUT_CSV, "r", encoding=ENCODING_IN, newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        artist = safe_str(row.get("artist", ""))
        album = safe_str(row.get("album", ""))
        track = safe_str(row.get("track", ""))
        utc_time = safe_str(row.get("utc_time", ""))

        if not artist or not track or not utc_time:
            continue

        dt = parse_lastfm_time(utc_time)

        if USE_ALBUM_IN_KEY:
            key = (artist.casefold(), album.casefold(), track.casefold())
        else:
            key = (artist.casefold(), track.casefold())

        if key not in tracks:
            tracks[key] = {
                "artist": artist,
                "album": album,
                "track": track,
                "playcount": 0,
                "first_played": dt,
                "last_played": dt,
            }

        tracks[key]["playcount"] += 1

        if dt < tracks[key]["first_played"]:
            tracks[key]["first_played"] = dt
        if dt > tracks[key]["last_played"]:
            tracks[key]["last_played"] = dt

# =========================
# ПОДГОТОВКА ВЫХОДА
# =========================

# Заголовки — максимально близко к iTunes TXT export
headers = [
    "Название",
    "Артист",
    "Композитор",
    "Альбом",
    "Группа",
    "Произведение",
    "Номер части",
    "Количество частей",
    "Название части",
    "Жанр",
    "Размер",
    "Длительность",
    "Номер диска",
    "Число дисков",
    "Номер дорожки",
    "Число дорожек",
    "Год",
    "Изменено",
    "Добавлено",
    "Битрейт",
    "Частота дискретизации",
    "Коррекция громкости",
    "Тип",
    "Эквалайзер",
    "Комментарии",
    "Воспроизведено",
    "Последнее исполнение",
    "Пропуски",
    "Последний пропуск",
    "Мой рейтинг",
    "Расположение",
]

rows = []

# Сортировка: сначала по артисту, потом по альбому, потом по треку
sorted_tracks = sorted(
    tracks.values(),
    key=lambda x: (
        x["artist"].casefold(),
        x["album"].casefold(),
        x["track"].casefold()
    )
)

for t in sorted_tracks:
    comments = (
        f"Last.fm scrobbles: {t['playcount']} | "
        f"First heard: {t['first_played'].strftime('%Y-%m-%d %H:%M')} | "
        f"Last heard: {t['last_played'].strftime('%Y-%m-%d %H:%M')}"
    )

    row = [
        t["track"],                                # Название
        t["artist"],                               # Артист
        "",                                        # Композитор
        t["album"],                                # Альбом
        "",                                        # Группа
        "",                                        # Произведение
        "",                                        # Номер части
        "",                                        # Количество частей
        "",                                        # Название части
        "",                                        # Жанр
        "",                                        # Размер
        "",                                        # Длительность
        "",                                        # Номер диска
        "",                                        # Число дисков
        "",                                        # Номер дорожки
        "",                                        # Число дорожек
        "",                                        # Год
        format_itunes_datetime(t["last_played"]),  # Изменено
        format_itunes_datetime(t["first_played"]), # Добавлено
        "",                                        # Битрейт
        "",                                        # Частота дискретизации
        "",                                        # Коррекция громкости
        "Аудиофайл MPEG",                          # Тип (заглушка)
        "",                                        # Эквалайзер
        comments,                                  # Комментарии
        str(t["playcount"]),                       # Воспроизведено
        format_itunes_datetime(t["last_played"]),  # Последнее исполнение
        "",                                        # Пропуски
        "",                                        # Последний пропуск
        "",                                        # Мой рейтинг
        "",                                        # Расположение
    ]

    rows.append(row)

# =========================
# ЗАПИСЬ
# =========================

with open(OUTPUT_TXT, "w", encoding=ENCODING_OUT, newline="") as f:
    writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    writer.writerows(rows)

print(f"Готово: {OUTPUT_TXT}")
print(f"Уникальных треков: {len(rows)}")