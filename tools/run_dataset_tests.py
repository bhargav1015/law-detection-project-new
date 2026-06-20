import json
import requests
from pathlib import Path

DATA_FILE = Path('backend/dataset.jsonl')
API = 'http://127.0.0.1:5000/analyze'

cases = []
with DATA_FILE.open('r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            cases.append(json.loads(line))
        except Exception as e:
            print('Failed to parse line:', line, e)

results = []
for i, item in enumerate(cases, start=1):
    case_text = item.get('caseText', '')
    expected_cat = item.get('category')
    expected_laws = [l.get('code') for l in item.get('laws', []) if l.get('code')]
    try:
        r = requests.post(API, data={'caseText': case_text}, timeout=30)
        rj = r.json() if r.status_code == 200 else {'error': r.text}
    except Exception as e:
        rj = {'error': str(e)}
    got_cat = rj.get('category')
    got_laws = [l.get('code') for l in rj.get('laws', [])] if isinstance(rj.get('laws'), list) else []
    cat_match = (expected_cat == got_cat)
    law_match = any(code in got_laws for code in expected_laws) if expected_laws else False
    results.append({'i': i, 'case': case_text[:120], 'expected_cat': expected_cat, 'got_cat': got_cat, 'cat_match': cat_match, 'expected_laws': expected_laws, 'got_laws': got_laws, 'law_match': law_match, 'raw_response': rj})

# Print summary
total = len(results)
cat_ok = sum(1 for r in results if r['cat_match'])
law_ok = sum(1 for r in results if r['law_match'])

print(f'Tested {total} cases. Category matches: {cat_ok}/{total}. Law matches: {law_ok}/{total}.')

print('\nFailures:')
for r in results:
    if not (r['cat_match'] and r['law_match']):
        print('-' * 80)
        print(f"#{r['i']}: {r['case']}")
        print(f" Expected category: {r['expected_cat']}, Got: {r['got_cat']}")
        print(f" Expected laws: {r['expected_laws']}")
        print(f" Got laws: {r['got_laws']}")
        print(f" Category match: {r['cat_match']}, Law match: {r['law_match']}")
        # print minimal raw response for debugging
        if isinstance(r['raw_response'], dict):
            print(' Raw response keys:', list(r['raw_response'].keys()))
        else:
            print(' Raw response:', r['raw_response'])

# Optionally write full results to a file
out_file = Path('tools/dataset_test_results.json')
with out_file.open('w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('\nDetailed results written to tools/dataset_test_results.json')
