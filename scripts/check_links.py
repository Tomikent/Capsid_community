"""Check every URL in the tool tables (*.tsv) and write a Markdown report.

Usage: python scripts/check_links.py [report.md]
Exits with status 1 if any link looks broken.

Some publishers (OUP, ScienceDirect, ...) reject automated access with 403/429
even when the page exists, so those are listed separately as "要確認" and are
not counted as broken.
"""
import glob
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

URL_COLUMNS = ('Link', 'Reference link', 'Kazumax')
USER_AGENT = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')
TIMEOUT = 30
BLOCKED_STATUS = (401, 403, 429, 503)


def collect_urls():
    """Return {url: [(file, line, name, column), ...]}."""
    urls = {}
    for path in sorted(glob.glob('*.tsv')):
        with open(path, encoding='utf-8') as f:
            lines = f.read().splitlines()
        header = lines[0].split('\t')
        for lineno, line in enumerate(lines[1:], start=2):
            row = dict(zip(header, line.split('\t')))
            for col, value in row.items():
                value = value.strip()
                if col.startswith(URL_COLUMNS) and value.startswith(('http://', 'https://')):
                    urls.setdefault(value, []).append((path, lineno, row.get('Name', '').strip(), col))
    return urls


def fetch(url):
    """Return (status, detail). status: 'ok' | 'blocked' | 'broken'."""
    last = ''
    for attempt in range(2):
        for method in ('HEAD', 'GET'):
            req = urllib.request.Request(url, method=method, headers={'User-Agent': USER_AGENT})
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
                    return 'ok', str(res.status)
            except urllib.error.HTTPError as e:
                last = f'HTTP {e.code}'
                if method == 'HEAD':
                    continue  # some servers do not support HEAD
                if e.code in BLOCKED_STATUS:
                    return 'blocked', last
                break
            except (urllib.error.URLError, socket.timeout, ConnectionError, ValueError) as e:
                last = str(getattr(e, 'reason', e))
                break
        time.sleep(3)
    return 'broken', last


def main():
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    out_path = sys.argv[1] if len(sys.argv) > 1 else 'link_report.md'

    urls = collect_urls()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = dict(zip(urls, pool.map(fetch, urls)))

    broken = [(u, d) for u, (s, d) in results.items() if s == 'broken']
    blocked = [(u, d) for u, (s, d) in results.items() if s == 'blocked']

    def rows(items):
        lines = ['|ツール|ファイル:行|列|URL|結果|', '|:---|:---|:---|:---|:---|']
        for url, detail in sorted(items, key=lambda x: urls[x[0]][0]):
            for path, lineno, name, col in urls[url]:
                lines.append(f'|{name}|{path}:{lineno}|{col}|{url}|{detail}|')
        return '\n'.join(lines)

    report = [f'{len(urls)} 件のリンクを確認しました。', '']
    report += [f'## リンク切れの可能性 ({len(broken)} 件)', '']
    report += [rows(broken) if broken else 'ありません。', '']
    report += [f'## 要確認：自動アクセスが拒否されたもの ({len(blocked)} 件)', '',
               '論文サイトなどはボットを拒否することが多く、ブラウザでは開ける場合がほとんどです。', '']
    report += [rows(blocked) if blocked else 'ありません。', '']
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f'checked={len(urls)} broken={len(broken)} blocked={len(blocked)} -> {out_path}')
    sys.exit(1 if broken else 0)


if __name__ == '__main__':
    main()
