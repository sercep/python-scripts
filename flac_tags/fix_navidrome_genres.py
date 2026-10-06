from pathlib import Path
from mutagen.flac import FLAC

# Путь к вашей музыкальной папке
MUSIC_ROOT = Path("music")

# True  -> запишет в GENRE и Primary, и Secondary жанры
# False -> запишет только Primary (основные) жанры
INCLUDE_SECONDARY = True

updated_count = 0

print("Сканирование FLAC-файлов на наличие тегов RYM...")

for flac_file in MUSIC_ROOT.rglob("*"):
    if flac_file.is_file() and flac_file.suffix.lower() == ".flac":
        try:
            audio = FLAC(flac_file)
            primary = audio.get("RYM_GENRE_PRIMARY", [])
            secondary = audio.get("RYM_GENRE_SECONDARY", [])

            if not primary and not secondary:
                continue

            genres = list(primary)
            if INCLUDE_SECONDARY:
                for s in secondary:
                    if s not in genres:
                        genres.append(s)

            if genres:
                audio["GENRE"] = genres
                audio.save()
                updated_count += 1
                print(f"[OK] {flac_file.name} -> {genres}")

        except Exception as e:
            print(f"[ERR] Ошибка в {flac_file.name}: {e}")

print(f"\nГотово! Обновлено треков: {updated_count}")