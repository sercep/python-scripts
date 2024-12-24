def remove_in_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
            all_text = ",".join(line.split(':', 1)[-1].strip() for line in infile)
            all_text = all_text.replace(" ", "")
            all_text = all_text.replace(",,", ",")
            outfile.write(all_text)
    print(f"Processed file saved to: {output_file}")

input_file = 'input.txt'
output_file = 'output.txt'
remove_in_file(input_file, output_file)