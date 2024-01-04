import glob
from datetime import datetime
from zoneinfo import ZoneInfo

tables = [
    ('ウイルス（ファージ）配列の予測(Prediction of viral and prophage sequences)', './Virus_prediction.tsv'),
    ('ゲノム(遺伝子)アノテーション(Genome/gene annotation tools)', './Annotation.tsv'),
    ('配列のClassification (系統分類) Taxonomic classification of viral sequences', './Classifier.tsv'),
    ('宿主予測 Host prediction', './Host_prediction.tsv'),
    ('CRISPR同定 Identification of host CRISPR sequences', './CRISPR_detection.tsv'),
    ('データベース Databases related to virology', './Database.tsv'),
    ('プラスミド様配列の検出 Plasmid detection', './Plasmid_detection.tsv'),
]

if __name__ == '__main__':

    readme_path = './README.md'
    output_path = './scripts/README.md'
    with open(readme_path, 'r') as f, open(output_path, 'w') as o:

        date = datetime.now(ZoneInfo('Asia/Tokyo'))

        tsv_paths = glob.glob('./*.tsv')

        is_tools_section = False
        for line in f.readlines():

            if line == '# Tools\n':
                is_tools_section = True
                o.write(line)
                o.write(f'<!-- The tables below were automatically generated at the {date} -->\n')
                for t in tables:
                    title, t_path = t
                    o.write('\n')
                    o.write(f'## {title}\n')

                    with open(t_path, 'r') as t_f:
                        header_cols = t_f.readline().strip().split('\t') # read and split a table header
                        col_number = len(header_cols)
                        header_str = '|' + '|'.join(header_cols) + '|\n'
                        o.write(header_str)
                        
                        separater = "|:---" * col_number + '|\n'
                        o.write(separater)

                        for row in t_f.readlines():
                            o.write('|' + row.strip().replace('\t', '|') + '|\n')
                        
                        o.write('\n')
            elif line.startswith('# '):
                is_tools_section = False
            
            if is_tools_section:
                continue

            o.write(line)
