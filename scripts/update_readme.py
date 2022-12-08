import glob
import datetime

def tsv2table(tsv_paths):
    tables = ''

    for path in tsv_paths:
        tables += '\n'
        with open(path, 'r') as f:
            title = f.readline() # read title
            tables += title
            
            header_cols = f.readline().strip().split('\t') # read and split a table header
            col_number = len(header_cols)
            header_str = '|' + '|'.join(header_cols) + '|\n'
            tables += header_str
            
            separater = "|:---" * col_number + '|\n'
            tables += separater

            for row in f.readlines():
                tables += '|' + row.strip().replace('\t','|') +'|\n'
            
            tables += '\n'

    return tables

if __name__ == '__main__':

    readme_path = './README.md'
    output_path = './scripts/README.md'
    with open(readme_path, 'r') as f, open(output_path, 'w') as o:

        date = datetime.datetime.now()

        tsv_paths = glob.glob('./*.tsv')
        tables = tsv2table(tsv_paths)

        for line in f.readlines():
            is_tools_section = False

            if line == '# Tools\n':
                is_tools_section = True
                o.write(line)
                o.write(f'<!-- The tables below were automatically generated at the {date} -->\n')
                o.write(tables)
            elif line.startswith('# '):
                is_tools_section = False
            
            if is_tools_section:
                continue

            o.write(line)