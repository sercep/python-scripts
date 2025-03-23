import re

def transform_paths(paths):
    transformed = []
    for path in paths:
        match = re.search(r'\\([^\\]+) \((\d{4})\)$', path)
        if match:
            title, year = match.groups()
            transformed.append((f"[[{title}, {year}]]", year))
        else:
            match = re.search(r'\\([^\\]+) \((Season \d+) - (\d{4}(?:-\d{4})?)\)$', path)
            if match:
                title, season, year = match.groups()
                transformed.append((f"[[{title}, {season}, {year}]]", year))
            else:
                match = re.search(r'\\([^\\]+) \((\d{4}-\d{4})\)$', path)
                if match:
                    title, years = match.groups()
                    transformed.append((f"[[{title}, {years}]]", years))
    return transformed

def read_paths_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines()]

def write_output_to_file(filename, data):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write("|     |     |\n| --- | --- |\n" + '\n'.join(f"| {entry} | {year} |" for entry, year in data))

input_filename = "input.txt"
output_filename = "output.txt"
paths = read_paths_from_file(input_filename)

result = transform_paths(paths)
write_output_to_file(output_filename, result)

print("|     |     |\n| --- | --- |")
for entry, year in result:
    print(f"| {entry} | {year} |")