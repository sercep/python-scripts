"""
rym_descriptor_tags.py

Автоматически сопоставляет JSON-экспорты дескрипторов (rym-descriptor-capture.user.js)
с альбомами в библиотеке music/. Поддерживает структуру music/<Artist>/<Album>/*.flac.

Записывает:
  - трековые дескрипторы -> тег MOOD
  - дескрипторы релиза целиком -> тег AlbumDescriptors
"""

import json
import re
import sys
import shutil
from pathlib import Path
from typing import Optional
from mutagen.flac import FLAC

# Путь к корню вашей музыки (измените при необходимости)
MUSIC_ROOT = Path("music")

# Папка, где скрипт ищет новые JSON (по умолчанию текущая папка и Загрузки)
DOWNLOAD_DIRS = [
    Path("."),
    Path.home() / "Downloads",
]


def clean_str(s: str) -> str:
    """Удаляет спецсимволы и приводит к нижнему регистру для сравнения."""
    return re.sub(r"[\W_]+", "", s.lower()) if s else ""


class LibraryIndex:
    """Индексирует папки с FLAC по тегам и путям."""

    def __init__(self, root: Path):
        self.root = root
        self.album_folders: list[dict] = []
        self._build_index()

    def _build_index(self):
        print(f"Сканирование библиотеки в {self.root}...")
        for flac_file in self.root.rglob("*.flac"):
            folder = flac_file.parent
            if any(item["path"] == folder for item in self.album_folders):
                continue

            try:
                audio = FLAC(flac_file)
                artist = audio.get("ALBUMARTIST", audio.get("ARTIST", [""]))[0]
                album = audio.get("ALBUM", [""])[0]
            except Exception:
                artist, album = "", ""

            self.album_folders.append({
                "path": folder,
                "artist": artist,
                "album": album,
                "clean_artist": clean_str(artist),
                "clean_album": clean_str(album),
                "folder_name": clean_str(folder.name),
                "parent_name": clean_str(folder.parent.name),
            })
        print(f"Найдено папок с альбомами: {len(self.album_folders)}")

    def find_album(self, artist_hint: str, album_hint: str) -> Optional[Path]:
        c_art = clean_str(artist_hint)
        c_alb = clean_str(album_hint)

        if c_alb:
            for item in self.album_folders:
                album_match = c_alb in item["clean_album"] or item["clean_album"] in c_alb
                artist_match = (
                    not c_art
                    or c_art in item["clean_artist"]
                    or item["clean_artist"] in c_art
                )
                if album_match and artist_match:
                    return item["path"]

        if c_alb:
            for item in self.album_folders:
                if c_alb in item["folder_name"] and (not c_art or c_art in item["parent_name"]):
                    return item["path"]

        return None

    def search_interactive(self, query: str) -> Optional[Path]:
        c_q = clean_str(query)
        matches = [
            item for item in self.album_folders
            if c_q in item["clean_album"] or c_q in item["clean_artist"] or c_q in item["folder_name"]
        ]
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]["path"]

        print("\nНайдено несколько совпадений:")
        for idx, m in enumerate(matches[:9], 1):
            rel = m["path"].relative_to(self.root)
            print(f"  [{idx}] {rel} ({m['artist']} - {m['album']})")

        choice = input("Выберите номер папки (Enter для пропуска): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(matches[:9]):
            return matches[int(choice) - 1]["path"]
        return None


def write_descriptor_tags(flac_path: Path, track_descriptors: list[str], album_descriptors: list[str]) -> None:
    """
    Пишет трековые дескрипторы в MOOD, а альбомные — в AlbumDescriptors (Vorbis comment).
    """
    audio = FLAC(flac_path)
    if track_descriptors:
        audio["MOOD"] = track_descriptors
    if album_descriptors:
        audio["AlbumDescriptors"] = album_descriptors
    audio.save()


def process_json_file(json_path: Path, lib: LibraryIndex) -> bool:
    print(f"\n--- Обработка: {json_path.name} ---")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    meta = data.pop("_meta", {})

    # Извлекаем дескрипторы релиза
    album_descriptors = data.pop("album", [])

    artist = meta.get("artist", "")
    album = meta.get("album", "")

    target_dir = None
    if artist or album:
        print(f"Метаданные из JSON: {artist} — {album}")
        target_dir = lib.find_album(artist, album)

    # Если автоматический поиск не помог или метаданных нет
    if not target_dir:
        print("Папка не найдена автоматически.")
        query = input("Введите название альбома/артиста для поиска (Enter для пропуска): ").strip()
        if not query:
            return False
        target_dir = lib.search_interactive(query)

    if not target_dir:
        print("Пропуск файла: папка не выбрана.")
        return False

    print(f"Целевая папка: {target_dir}")
    if album_descriptors:
        print(f"Альбомные дескрипторы ({len(album_descriptors)} шт.): {', '.join(album_descriptors[:6])}...")

    # Собираем треки в папке
    flac_by_track = {}
    for f in target_dir.rglob("*.flac"):
        try:
            num = FLAC(f).get("TRACKNUMBER", ["0"])[0].split("/")[0].split("-")[-1].lstrip("0") or "0"
            flac_by_track[num] = f
        except Exception:
            continue

    applied_count = 0
    for scope, descriptors in data.items():
        flac_path = flac_by_track.get(scope)
        if not flac_path:
            print(f"  [!] Трек #{scope} не найден во FLAC")
            continue

        write_descriptor_tags(flac_path, descriptors, album_descriptors)
        print(f"  Трек {scope:>2}: {flac_path.name[:35]:<35} | {', '.join(descriptors[:4])}{'...' if len(descriptors) > 4 else ''}")
        applied_count += 1

    print(f"Успешно размечено треков: {applied_count}")

    # Перемещаем обработанный JSON в processed
    processed_dir = json_path.parent / "processed"
    processed_dir.mkdir(exist_ok=True)
    shutil.move(str(json_path), str(processed_dir / json_path.name))
    print(f"JSON перемещен в {processed_dir / json_path.name}")
    return True


def collect_json_targets() -> list[Path]:
    """Собирает JSON-файлы из аргументов командной строки или сканирует папки."""
    if len(sys.argv) > 1:
        return [Path(p) for p in sys.argv[1:] if Path(p).is_file() and p.endswith(".json")]

    found = []
    for d in DOWNLOAD_DIRS:
        if d.exists():
            found.extend(list(d.glob("rym-descriptors-*.json")))
    return found


def main():
    if not MUSIC_ROOT.exists():
        print(f"Ошибка: корневая папка '{MUSIC_ROOT}' не найдена. Проверьте путь MUSIC_ROOT в начале скрипта.")
        return

    json_files = collect_json_targets()
    if not json_files:
        print("Новых файлов rym-descriptors-*.json не найдено.")
        return

    print(f"Найдено JSON-файлов для обработки: {len(json_files)}")
    lib = LibraryIndex(MUSIC_ROOT)

    for jf in json_files:
        try:
            process_json_file(jf, lib)
        except Exception as e:
            print(f"Ошибка при обработке {jf.name}: {e}")


if __name__ == "__main__":
    main()