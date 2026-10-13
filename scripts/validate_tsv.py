"""Check the tool tables (*.tsv) for formatting mistakes.

Usage: python scripts/validate_tsv.py
Exits with status 1 if any error is found. On GitHub Actions the errors are
also shown as annotations on the offending lines.
"""
import glob
import os
import re
import sys

from update_readme import tables

CODE_HOSTS = ('github.com', 'gitlab.com', 'bitbucket.org', 'sourceforge.net')
IN_ACTIONS = os.environ.get('GITHUB_ACTIONS') == 'true'


def report(errors, path, line, msg):
    errors.append((path, line, msg))
    if IN_ACTIONS:
        print(f'::error file={path},line={line}::{msg}')


def check_file(path, errors):
    with open(path, encoding='utf-8', newline='') as f:
        lines = [l.rstrip('\r\n') for l in f]
    if not lines:
        report(errors, path, 1, 'ファイルが空です')
        return
    header = lines[0].split('\t')
    n_cols = len(header)
    seen = {}

    for lineno, line in enumerate(lines[1:], start=2):
        if line.strip() == '':
            report(errors, path, lineno, '空行があります')
            continue
        cells = line.split('\t')
        if len(cells) != n_cols:
            report(errors, path, lineno,
                   f'列数が {len(cells)} です（ヘッダは {n_cols} 列）。タブの数を確認してください')
        row = dict(zip(header, cells))
        name = row.get('Name', '')

        for col, value in row.items():
            if value != value.strip():
                report(errors, path, lineno, f'{col} 列の前後に空白があります: {value!r}')
            value = value.strip()
            if not value:
                continue
            if col in ('Link', 'Reference link') and not value.startswith(('http://', 'https://')):
                report(errors, path, lineno, f'{col} 列が URL ではありません: {value!r}')
            if col == 'Reference link' and any(h in value for h in CODE_HOSTS):
                report(errors, path, lineno,
                       f'Reference link 列にコードの URL があります（Link 列と逆では？）: {value}')
            if col.startswith('Kazumax') and 'kazumaxneo.hatenablog.com' not in value:
                report(errors, path, lineno,
                       f'{col} 列に kazumaxneo のブログ以外が入っています（列ずれでは？）: {value!r}')
            if col == 'Release' and not re.fullmatch(r'\d{4}', value):
                report(errors, path, lineno,
                       f'Release 列は西暦 4 桁にしてください（補足は Note 列へ）: {value!r}')

        key = name.strip().lower()
        if not key:
            report(errors, path, lineno, 'Name 列が空です')
        elif key in seen:
            report(errors, path, lineno, f'{name.strip()} が {seen[key]} 行目と重複しています')
        else:
            seen[key] = lineno


def main():
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    os.chdir(root)
    errors = []

    listed = {os.path.normpath(p) for _, p in tables}
    for path in sorted(glob.glob('*.tsv')):
        if os.path.normpath(path) not in listed:
            report(errors, path, 1, 'scripts/update_readme.py の tables に登録されていないので README に表示されません')
        check_file(path, errors)

    if errors:
        if not IN_ACTIONS:
            for path, line, msg in errors:
                print(f'{path}:{line}: {msg}')
        print(f'\n{len(errors)} 件の問題が見つかりました')
        sys.exit(1)
    print('OK: 問題は見つかりませんでした')


if __name__ == '__main__':
    main()
