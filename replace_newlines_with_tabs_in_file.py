def replace_newlines_with_tabs(text):
    newtext = text.replace('\n\n\n', '\t')
    newtext = newtext.replace('\t\t', '\t')
    newtext = newtext.replace('releases', '')
    return newtext

def replace_newlines_with_tabs_in_file(input_file, output_file):
    with open(input_file, 'r') as f:
        text = f.read()

    modified_text = replace_newlines_with_tabs(text)

    with open(output_file, 'w') as f:
        f.write(modified_text)

input_file = 'input.txt'
output_file = 'output.txt'
replace_newlines_with_tabs_in_file(input_file, output_file)