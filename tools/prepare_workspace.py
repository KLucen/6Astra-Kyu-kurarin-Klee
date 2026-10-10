"""Relocate source_meta.json after verifying the archived source video hash."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def relocate(metadata_path, source, apply=False):
    metadata = json.loads(metadata_path.read_text(encoding='utf-8-sig'))
    source = source.resolve(strict=True)
    with source.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != metadata['sha256']:
        raise ValueError('Source SHA-256 differs from the recorded production source')
    new_path = str(source)
    changed = metadata['source'] != new_path
    result = {'source': new_path, 'sha256': actual, 'path_change_needed': changed, 'applied': False}
    if apply and changed:
        backup = metadata_path.with_name('source_meta.archive.json')
        if not backup.exists():
            with backup.open('xb') as stream:
                stream.write(metadata_path.read_bytes())
        metadata['source'] = new_path
        temporary = metadata_path.with_name('source_meta.relocating.json')
        with temporary.open('x', encoding='utf-8') as stream:
            json.dump(metadata, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.replace(temporary, metadata_path)
        result['applied'] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source', type=Path, help='Optional relocated copy of the same source video')
    parser.add_argument('--apply', action='store_true', help='Write only the source path; preserve original metadata backup')
    args = parser.parse_args()
    manifest = json.loads((args.root / 'ARCHIVE_MANIFEST.json').read_text(encoding='utf-8'))
    source = args.source or args.root / manifest['source_video']
    metadata_path = args.root / 'klee_kyukurarin/analysis/source_meta.json'
    print(json.dumps(relocate(metadata_path, source, args.apply), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
