from bs4 import BeautifulSoup
import os
import sys
from time import time

INPUT_FILE = 'suspender.html'
OUTPUT_FILE = 'suspender_links.md'

# Проверяем наличие файла
print(f"Проверка файла: {INPUT_FILE}", flush=True)
if not os.path.exists(INPUT_FILE):
    print(f"Файл не найден: {INPUT_FILE}", flush=True)
    sys.exit(1)

# Читаем файл
start_time = time()
print("Чтение HTML-файла...", flush=True)
with open(INPUT_FILE, 'r', encoding='windows-1252', errors='ignore') as f:
    html = f.read()
print(f"Файл прочитан за {time() - start_time:.1f} сек, размер {len(html)/1024/1024:.1f} МБ", flush=True)

# Парсим HTML
start_time = time()
print("Парсинг HTML (html.parser)...", flush=True)
soup = BeautifulSoup(html, 'html.parser')  # используем встроенный парсер
print(f"Парсинг завершён за {time() - start_time:.1f} сек", flush=True)

sessions = soup.select(".sessionContainer")
total_sessions = len(sessions)
print(f"Найдено сессий: {total_sessions}", flush=True)

# Приготовим вывод
markdown_output = []

for s_idx, session in enumerate(sessions, start=1):
    print(f"Обработка сессии {s_idx}/{total_sessions}", flush=True)
    # Заголовок сессии
    session_title = session.select_one(".sessionLink")
    if session_title:
        markdown_output.append(f"## {session_title.text.strip()}")

    # Содержимое сессии
    contents = session.select_one(".sessionContents")
    if not contents:
        print(f"  ! Нет .sessionContents в сессии {s_idx}", flush=True)
        markdown_output.append("")
        continue

    # Ищем окна и вкладки среди прямых детей
    children = contents.find_all(recursive=False)
    windows = [el for el in children if 'windowContainer' in el.get('class', [])]
    print(f"  Окна: {len(windows)}", flush=True)

    win_idx = 0
    for elem in children:
        if 'windowContainer' in elem.get('class', []):
            win_idx += 1
            title = elem.get_text(strip=True) or f"Окно {win_idx}"
            print(f"    Окно {win_idx}/{len(windows)}: {title}", flush=True)
            markdown_output.append(f"### {title}")
        elif 'tabContainer' in elem.get('class', []):
            link = elem.select_one('.historyLink')
            if link and link.get('href'):
                markdown_output.append(f"- [{link.text.strip()}]({link['href']})")
    markdown_output.append("")

# Запись результата
print(f"Запись результата в {OUTPUT_FILE}...", flush=True)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write("\n".join(markdown_output))
print(f"Готово! Записано {len(markdown_output)} строк", flush=True)
