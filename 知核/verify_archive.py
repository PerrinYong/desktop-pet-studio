"""Read-only verification of all archived files; standard library only."""
from pathlib import Path
import hashlib, json, sys
root = Path(__file__).resolve().parent
data = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
errors = []
skipped_local_only = []
checked_files = 0
for entry in data['files']:
    path = root / entry['path']
    if not path.is_file():
        if entry.get('local_only', False):
            skipped_local_only.append(entry['path'])
            continue
        errors.append({'path': entry['path'], 'error': 'missing'})
        continue
    checked_files += 1
    with path.open('rb') as f:
        h = hashlib.file_digest(f, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else hashlib.sha256(f.read()).hexdigest()
    if h != entry['sha256'] or path.stat().st_size != entry['bytes']:
        errors.append({'path': entry['path'], 'error': 'hash-or-size-mismatch'})
print(json.dumps({'ok': not errors, 'checked_files': checked_files, 'skipped_local_only': skipped_local_only, 'errors': errors}, ensure_ascii=False, indent=2))
sys.exit(bool(errors))
