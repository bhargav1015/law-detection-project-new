import csv
import json
import argparse
import os

TEMPLATE_CSV = 'backend/dataset_template.csv'
OUTPUT_JSONL = 'backend/dataset.jsonl'


def validate_entry(entry: dict) -> bool:
    # basic schema validation: require caseText and category and laws as list
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


def csv_to_jsonl(csv_path: str, out_path: str):
    written = 0
    with open(csv_path, newline='', encoding='utf-8') as csvfile, open(out_path, 'w', encoding='utf-8') as out:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                laws = json.loads(row.get('laws_json', '[]'))
                defenses = json.loads(row.get('defenses_json', '[]'))
                reasons = json.loads(row.get('reasons_json', '{}'))
                followUps = json.loads(row.get('followUps_json', '[]'))
            except Exception as e:
                print('Skipping row due to JSON parse error:', e)
                continue
            entry = {
                'caseText': row.get('caseText', '').strip(),
                'category': row.get('category', '').strip(),
                'laws': laws,
                'defenses': defenses,
                'reasons': reasons,
                'followUps': followUps,
                'notes': row.get('notes', '').strip()
            }
            if validate_entry(entry):
                out.write(json.dumps(entry, ensure_ascii=False) + '\n')
                written += 1
            else:
                print('Invalid entry skipped:', entry.get('caseText')[:80])
    print(f'Wrote {written} entries to {out_path}')


def interactive_add(out_path: str):
    print('Interactive dataset entry. Press enter to quit at any prompt.')
    while True:
        case = input('Case text: ').strip()
        if not case:
            break
        category = input('Category (Criminal/Civil/Uncategorized): ').strip() or 'Uncategorized'
        laws_raw = input('Laws as JSON (e.g. [{"code":"IPC 378","desc":"Theft"}]): ').strip() or '[]'
        defenses_raw = input('Defenses as JSON array: ').strip() or '[]'
        reasons_raw = input('Reasons as JSON object: ').strip() or '{}'
        followups_raw = input('FollowUps as JSON array: ').strip() or '[]'
        notes = input('Notes (optional): ').strip()
        try:
            laws = json.loads(laws_raw)
            defenses = json.loads(defenses_raw)
            reasons = json.loads(reasons_raw)
            followUps = json.loads(followups_raw)
        except Exception as e:
            print('JSON parse error:', e)
            continue
        entry = {
            'caseText': case,
            'category': category,
            'laws': laws,
            'defenses': defenses,
            'reasons': reasons,
            'followUps': followUps,
            'notes': notes
        }
        if not validate_entry(entry):
            print('Entry failed validation, not saved.')
            continue
        with open(out_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        print('Saved entry.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Collect or convert labeled dataset for law detector')
    parser.add_argument('--from-csv', help='Convert CSV to JSONL', action='store_true')
    parser.add_argument('--csv', help='CSV file path', default=TEMPLATE_CSV)
    parser.add_argument('--out', help='Output JSONL path', default=OUTPUT_JSONL)
    parser.add_argument('--interactive', help='Add entries interactively', action='store_true')
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    if args.from_csv:
        csv_to_jsonl(args.csv, args.out)
    if args.interactive:
        interactive_add(args.out)
