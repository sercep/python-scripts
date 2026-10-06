"""
obsidian_note_tags.py

Читает countries / languages / наличие "instrumental" из YAML-frontmatter
заметки Obsidian и пишет их в FLAC-теги подходящего альбома в библиотеке:
  countries (список в YAML)        -> ARTIST_COUNTRY (multi-valued)
  languages (список в YAML)        -> LANGUAGE (multi-valued)
  "instrumental" в rym tags (да/нет) -> INSTRUMENTAL = "true" / "false"

В отличие от скриптов на основе JSON от RYM, заметки не двигаются и не
помечаются обработанными -- это ваши постоянные файлы в Obsidian. Повторный
запуск просто перезапишет теги тем, что сейчас в заметке (пригодится,
если что-то поправите в YAML и захотите синхронизировать заново).

Своей страницы под каждую из трёх меток у Navidrome нет -- нужно добавить
кастомные теги в navidrome.toml:
    Tags.artist_country.Aliases = ["artist_country"]
    Tags.language.Aliases = ["language"]
    Tags.instrumental.Aliases = ["instrumental"]
и затем full scan.

Нужно: pip install mutagen pyyaml --break-system-packages
"""

import re
import sys
import shutil
from pathlib import Path
from typing import Optional

import yaml
from mutagen.flac import FLAC

# Где лежат .md-заметки релизов -- поправьте под структуру своего вулта
NOTES_ROOT = [
    Path("."),
    Path.home() / "Downloads",
]

# Корень музыкальной библиотеки (как в rym_genre_tags.py / rym_descriptor_tags.py)
MUSIC_ROOT = Path("music")

# Имя файла заметки: "Artist - Title (Year).md" -- отдельного поля под
# название релиза в YAML нет, так что название берём из имени файла.
FILENAME_RE = re.compile(r"^(?P<artist>.+?) - (?P<title>.+) \((?P<year>\d{4})\)$")


def clean_str(s: str) -> str:
    """Удаляет спецсимволы и приводит к нижнему регистру для сравнения."""
    return re.sub(r"[\W_]+", "", s.lower()) if s else ""


def clean_wikilink(s: str) -> str:
    """"[[lilen]]" -> "lilen"; "[[note|Display Name]]" -> "Display Name"."""
    s = s.strip().strip("[]").strip()
    if "|" in s:
        s = s.split("|", 1)[1].strip()
    return s


class LibraryIndex:
    """Та же логика, что в rym_genre_tags.py / rym_descriptor_tags.py --
    при использовании всех трёх скриптов стоит вынести в общий модуль."""

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


def extract_frontmatter(md_text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", md_text, re.DOTALL)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def parse_note(md_path: Path) -> Optional[dict]:
    text = md_path.read_text(encoding="utf-8")
    fm = extract_frontmatter(text)
    if not fm:
        print(f"  [!] Нет YAML-frontmatter: {md_path.name}")
        return None

    m = FILENAME_RE.match(md_path.stem)
    file_artist = m.group("artist") if m else ""
    title = m.group("title") if m else ""

    artists_yaml = fm.get("artists") or []
    artist = clean_wikilink(artists_yaml[0]) if artists_yaml else file_artist

    countries = fm.get("countries") or []
    languages = fm.get("languages") or []
    rym_tags = fm.get("rym tags") or []
    instrumental = any(str(t).strip().lower() == "instrumental" for t in rym_tags)

    return {
        "artist": artist,
        "title": title,
        "countries": [str(c) for c in countries],
        "languages": [str(lang) for lang in languages],
        "instrumental": instrumental,
    }


def write_release_tags(flac_path: Path, countries: list[str], languages: list[str], instrumental: bool) -> None:
    audio = FLAC(flac_path)
    if countries:
        audio["ARTIST_COUNTRY"] = countries
    if languages:
        audio["LANGUAGE"] = languages
    audio["INSTRUMENTAL"] = ["true" if instrumental else "false"]
    audio.save()


def process_note(md_path: Path, lib: LibraryIndex) -> bool:
    print(f"\n--- {md_path.name} ---")
    data = parse_note(md_path)
    if data is None:
        return False

    print(f"  artist={data['artist']!r} title={data['title']!r} "
          f"countries={data['countries']} languages={data['languages']} "
          f"instrumental={data['instrumental']}")

    target_dir = lib.find_album(data["artist"], data["title"])
    if not target_dir:
        print("  [!] Папка альбома не найдена, пропуск")
        return False

    flac_files = list(target_dir.rglob("*.flac"))
    if not flac_files:
        print(f"  [!] FLAC не найдены в {target_dir}")
        return False

    for f in flac_files:
        write_release_tags(f, data["countries"], data["languages"], data["instrumental"])
    print(f"  Размечено файлов: {len(flac_files)} в {target_dir}")

    # Перемещаем обработанную заметку в подпапку processed
    processed_dir = md_path.parent / "processed"
    processed_dir.mkdir(exist_ok=True)
    shutil.move(str(md_path), str(processed_dir / md_path.name))
    print(f"  Заметка перемещена в {processed_dir / md_path.name}")

    return True


def collect_note_targets() -> list[Path]:
    """Заметки из аргументов командной строки, либо все *.md в папках из NOTES_ROOT."""
    if len(sys.argv) > 1:
        return [Path(p) for p in sys.argv[1:] if Path(p).suffix.lower() == ".md" and Path(p).is_file()]

    # Поддерживаем как один Path, так и список путей
    search_dirs = NOTES_ROOT if isinstance(NOTES_ROOT, (list, tuple)) else [NOTES_ROOT]

    found = []
    for d in search_dirs:
        if d.exists() and d.is_dir():
            # Если заметки лежат в подпапках хранилища Obsidian, замените glob на rglob
            found.extend(d.glob("*.md"))

    # Убираем возможные дубликаты путей и сортируем
    unique_notes = sorted(list({p.resolve(): p for p in found}.values()))
    return unique_notes


def main():
    if not MUSIC_ROOT.exists():
        print(f"Ошибка: корневая папка '{MUSIC_ROOT}' не найдена. Проверьте MUSIC_ROOT в начале скрипта.")
        return

    notes = collect_note_targets()
    if not notes:
        print("Заметок для обработки не найдено.")
        return

    print(f"Найдено заметок: {len(notes)}")
    lib = LibraryIndex(MUSIC_ROOT)

    ok = 0
    for note in notes:
        try:
            if process_note(note, lib):
                ok += 1
        except Exception as e:
            print(f"Ошибка при обработке {note.name}: {e}")
    print(f"\nГотово: {ok} / {len(notes)} заметок применено.")


if __name__ == "__main__":
    main()