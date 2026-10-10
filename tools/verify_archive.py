"""Verify the exact bytes of every file in the engineering archive manifest."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(root, manifest):
    root = root.resolve()
    seen, errors = set(), []
    entries = manifest['files']
    if not entries:
        raise ValueError('Empty archive manifest')
    for item in entries:
        relative = PurePosixPath(item['path'])
        if relative.is_absolute() or '..' in relative.parts or '\\' in item['path'] or ':' in item['path']:
            raise ValueError(f'Unsafe archive path: {relative}')
        if item['path'] in seen:
            raise ValueError(f'Duplicate manifest entry: {relative}')
        seen.add(item['path'])
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f'Path escapes archive: {relative}')
        if not path.is_file():
            errors.append({'path': str(relative), 'error': 'missing'})
        elif path.stat().st_size != item['bytes']:
            errors.append({'path': str(relative), 'error': 'size mismatch'})
        elif digest(path) != item['sha256']:
            errors.append({'path': str(relative), 'error': 'SHA-256 mismatch'})
    return {'checked_files': len(entries), 'checked_bytes': sum(x['bytes'] for x in entries),
            'errors': errors, 'archive_pass': not errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    manifest = json.loads((args.root / 'ARCHIVE_MANIFEST.json').read_text(encoding='utf-8'))
    result = verify(args.root, manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['archive_pass'] else 1)


if __name__ == '__main__':
    main()
