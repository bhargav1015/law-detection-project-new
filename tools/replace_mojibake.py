import os
import io

ROOT = os.path.dirname(os.path.dirname(__file__))
# mappings of mojibake -> replacement
MAPPINGS = {
    'â€“': '–',  # en dash
    'â€”': '—',  # em dash
    'â€˜': '‘',  # left single quote
    'â€™': '’',  # right single quote
    'â€œ': '“',  # left double quote
    'â€': '"',
    'â': '"',
    'â€': '"',
    'â€': '"',
    'â€¦': '…'
}

TEXT_EXTS = {'.html', '.htm', '.js', '.css', '.md', '.txt', '.py'}

changed_files = []

for dirpath, dirnames, filenames in os.walk(ROOT):
    # skip .git and venv folders
    if any(p in dirpath for p in ['.git', '.venv', 'venv', 'node_modules']):
        continue
    for fn in filenames:
        _, ext = os.path.splitext(fn)
        if ext.lower() not in TEXT_EXTS:
            continue
        path = os.path.join(dirpath, fn)
        try:
            with io.open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            # try latin-1 then decode/encode
            try:
                with io.open(path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception:
                continue
        new = content
        for k, v in MAPPINGS.items():
            if k in new:
                new = new.replace(k, v)
        if new != content:
            with io.open(path, 'w', encoding='utf-8') as f:
                f.write(new)
            changed_files.append(path)

print('Changed files:')
for p in changed_files:
    print(p)
print('Done. Total changed:', len(changed_files))
