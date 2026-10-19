"""Check the standalone requirements/specs input set; no runtime dependencies."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'specs/inputs.manifest.json'


def snapshot():
    paths = [ROOT / 'Requirments.md']
    for path in (ROOT / 'specs').rglob('*'):
        if '__pycache__' in path.parts:
            continue
        if path.is_symlink():
            raise ValueError(f'Symlink is not an input: {path}')
        if path.is_file() and path != MANIFEST:
            paths.append(path)
    files = {}
    for path in sorted(paths):
        if path.is_symlink():
            raise ValueError(f'Symlink is not an input: {path}')
        data = path.read_bytes()
        text = data.decode('utf-8')
        if path.suffix == '.json':
            data = json.dumps(json.loads(text), sort_keys=True,
                              separators=(',', ':'), ensure_ascii=True).encode()
        elif '\r' in text:
            raise ValueError(f'Expected LF line endings: {path}')
        files[path.relative_to(ROOT).as_posix()] = hashlib.sha256(data).hexdigest()
    return {'format_version': 1, 'files': files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update', action='store_true', help='Write reviewed input hashes')
    args = parser.parse_args()
    try:
        expected = snapshot()
        if args.update:
            MANIFEST.write_text(json.dumps(expected, indent=2) + '\n', encoding='utf-8')
            print(f"Updated {len(expected['files'])} input hashes")
            return 0
        actual = json.loads(MANIFEST.read_text(encoding='utf-8'))
        if actual != expected:
            print('Input manifest mismatch; review changes before --update')
            return 1
        print(f"Verified {len(expected['files'])} inputs")
        return 0
    except (OSError, ValueError) as exc:
        print(f'Invalid inputs: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
