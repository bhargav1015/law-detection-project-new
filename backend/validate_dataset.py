import json
import argparse


def validate_entry(entry: dict) -> bool:
    if 'caseText' not in entry or not entry['caseText'].strip():
        return False
    if 'category' not in entry or not entry['category'].strip():
        return False
    if 'laws' not in entry or not isinstance(entry['laws'], list):
        return False
    for l in entry['laws']:
        if not isinstance(l, dict) or 'code' not in l or 'desc' not in l:
            return False
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Validate JSONL dataset')
    parser.add_argument('--file', default='backend/dataset.jsonl')
    args = parser.parse_args()

    total = 0
    valid = 0
    invalid = 0
    with open(args.file, encoding='utf-8') as f:
        for line in f:
            total += 1
            try:
                obj = json.loads(line)
            except Exception:
                invalid += 1
                continue
            if validate_entry(obj):
                valid += 1
            else:
                invalid += 1
    print(f'Total: {total}, Valid: {valid}, Invalid: {invalid}')
