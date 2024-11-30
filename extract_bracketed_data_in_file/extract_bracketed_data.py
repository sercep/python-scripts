import re

def extract_bracketed_data(text):
    newtext = re.findall(r'\[([^\]]*)\]', text)
    result = '\n'.join(newtext)
    return result 

def extract_bracketed_data_in_file(input_file, output_file):
    with open(input_file, 'r') as f:
        text = f.read()

    modified_text = extract_bracketed_data(text)

    with open(output_file, 'w') as f:
        f.write(modified_text)

input_file = 'input1.txt'
output_file = 'output1.txt'
extract_bracketed_data_in_file(input_file, output_file)

input_file = 'input2.txt'
output_file = 'output2.txt'
extract_bracketed_data_in_file(input_file, output_file)