import re
import sys
import os
from collections import defaultdict, Counter

def parse_markdown_links(md_text):
    # Matches lines like: - [text](url)
    pattern = re.compile(r"^- \[(?P<text>.*?)\]\((?P<url>.*?)\)")
    for lineno, line in enumerate(md_text.splitlines(), start=1):
        m = pattern.match(line)
        if m:
            yield lineno, m.group('url'), m.group('text')


def generate_duplicate_report(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        sys.exit(1)

    text = open(input_file, encoding='utf-8').read()
    entries = list(parse_markdown_links(text))

    # Count occurrences and collect titles per URL
    url_counts = Counter()
    url_titles = defaultdict(set)
    url_lines = defaultdict(list)

    for lineno, url, title in entries:
        url_counts[url] += 1
        url_titles[url].add(title)
        url_lines[url].append(lineno)

    # Filter duplicates
    duplicates = [(url, cnt) for url, cnt in url_counts.items() if cnt > 1]
    if not duplicates:
        print("No duplicates found.")
        return

    # Sort by descending count
    duplicates.sort(key=lambda x: x[1], reverse=True)

    # Write report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Duplicate Links Report\n")
        f.write(f"Input: {input_file}\n")
        f.write(f"Total duplicate URLs: {len(duplicates)}\n\n")
        for url, cnt in duplicates:
            titles = url_titles[url]
            lines = url_lines[url]
            f.write(f"## {url}\n")
            f.write(f"- Count: {cnt}\n")
            f.write(f"- Titles: {', '.join(sorted(titles))}\n")
            f.write(f"- Lines: {', '.join(map(str, lines))}\n\n")

    print(f"Report written to {output_file}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate duplicate links report from a Markdown file')
    parser.add_argument('input', nargs='?', default='suspender_links.md', help='Input Markdown file')
    parser.add_argument('-o', '--output', default='duplicates_report.md', help='Output report file')
    args = parser.parse_args()

    generate_duplicate_report(args.input, args.output)
