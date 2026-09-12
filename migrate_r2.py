#!/usr/bin/env python3
"""将 Cloudflare R2 文件柜 (agi-pm-files) 的全部对象迁移到本地磁盘。
用法（在腾讯云服务器上执行）：
  export CLOUDFLARE_API_TOKEN=...
  export CF_ACCOUNT_ID=3dd7bef80dfcb458db4f28ed47710b12
  export R2_BUCKET=agi-pm-files
  python3 /home/ubuntu/migrate_r2.py
"""
import os, sys, json, urllib.request, urllib.parse, ssl, pathlib

TOKEN = os.environ.get('CLOUDFLARE_API_TOKEN', '')
ACCOUNT_ID = os.environ.get('CF_ACCOUNT_ID', '3dd7bef80dfcb458db4f28ed47710b12')
BUCKET = os.environ.get('R2_BUCKET', 'agi-pm-files')
ROOT_DIR = os.environ.get('LOCAL_FILES_ROOT', '/home/ubuntu/node-backend/data/files')

if not TOKEN:
    print('ERROR: CLOUDFLARE_API_TOKEN is required')
    sys.exit(1)

BASE_URL = f'https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/r2/buckets/{BUCKET}'
CTX = ssl.create_default_context()


def api_get(path):
    url = BASE_URL + path
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {TOKEN}'})
    with urllib.request.urlopen(req, context=CTX) as r:
        return json.loads(r.read().decode('utf-8'))


def download_object(key):
    encoded = urllib.parse.quote(key, safe='')
    url = f'{BASE_URL}/objects/{encoded}'
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {TOKEN}'})
    with urllib.request.urlopen(req, context=CTX) as r:
        data = r.read()
        ctype = r.headers.get('Content-Type', 'application/octet-stream')
        return data, ctype


def key_to_local_path(key):
    parts = [p.replace('\\', '_').replace('/', '_').replace(':', '_').replace('*', '_')
             .replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_')
             .replace('|', '_') for p in key.split('/')]
    return pathlib.Path(ROOT_DIR).joinpath(*parts)


def list_objects():
    cursor = ''
    all_objs = []
    while True:
        path = '/objects?limit=1000'
        if cursor:
            path += f'&cursor={urllib.parse.quote(cursor)}'
        data = api_get(path)
        result = data.get('result', {})
        if isinstance(result, list):
            objs = result
            truncated = len(objs) == 1000
            cursor = objs[-1].get('key', '') if objs else ''
        else:
            objs = result.get('objects', [])
            truncated = result.get('truncated', False)
            cursor = result.get('cursor', '')
        all_objs.extend(objs)
        if not truncated:
            break
        if not cursor:
            break
    return all_objs


def main():
    print(f'Listing objects from R2 bucket: {BUCKET}')
    objs = list_objects()
    print(f'Total objects: {len(objs)}')
    if not objs:
        return

    pathlib.Path(ROOT_DIR).mkdir(parents=True, exist_ok=True)
    downloaded = 0
    skipped = 0
    failed = 0
    total_bytes = 0

    for o in objs:
        key = o.get('key', '')
        size = o.get('size', 0)
        if not key:
            continue
        local_file = key_to_local_path(key)
        meta_file = pathlib.Path(str(local_file) + '.meta.json')

        # 已存在且大小一致则跳过
        if local_file.exists() and local_file.stat().st_size == size and meta_file.exists():
            print(f'[SKIP] {key}')
            skipped += 1
            continue

        try:
            print(f'[DOWN] {key} ({size} bytes)')
            data, ctype = download_object(key)
            local_file.parent.mkdir(parents=True, exist_ok=True)
            with open(local_file, 'wb') as f:
                f.write(data)
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump({'contentType': ctype}, f)
            downloaded += 1
            total_bytes += len(data)
        except Exception as e:
            print(f'[FAIL] {key}: {e}')
            failed += 1

    print(f'\nDone. downloaded={downloaded}, skipped={skipped}, failed={failed}, bytes={total_bytes}')


if __name__ == '__main__':
    main()
