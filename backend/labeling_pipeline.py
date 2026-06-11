import os
import sys
import json
import subprocess
import runpy

ROOT = os.path.dirname(os.path.dirname(__file__))
UNLABELED = os.path.join(ROOT, 'backend', 'unlabeled.jsonl')
PROPOSED = os.path.join(ROOT, 'backend', 'proposed_labels.jsonl')
REVIEWED = os.path.join(ROOT, 'backend', 'dataset_reviewed.jsonl')
DATASET = os.path.join(ROOT, 'backend', 'dataset.jsonl')

def run_auto_label():
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        print('OPENAI_API_KEY not set — skipping auto-label step.')
        return
    if not os.path.exists(UNLABELED):
        print(f'No unlabeled file at {UNLABELED}; create one with one JSON per line with a caseText field.')
        return
    print('Running auto-label (LLM proposals) — this may take time...')
    subprocess.run([sys.executable, os.path.join(ROOT, 'backend', 'auto_label.py')], check=False)

def run_reviewer():
    if not os.path.exists(PROPOSED):
        print('No proposals found at', PROPOSED)
        print('If you ran auto-label just now, ensure it completed successfully.')
        # still allow running reviewer manually if REVIEWED exists
    print('Launching interactive reviewer (accept/edit/skip).')
    subprocess.run([sys.executable, os.path.join(ROOT, 'backend', 'review_labels.py')])

def merge_reviewed_and_retrain():
    # ensure dataset exists
    os.makedirs(os.path.dirname(DATASET), exist_ok=True)
    if not os.path.exists(DATASET):
        open(DATASET, 'w', encoding='utf-8').close()

    existing = set()
    with open(DATASET, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                o = json.loads(line)
                existing.add(o.get('caseText','').strip())
            except Exception:
                continue

    merged = 0
    if os.path.exists(REVIEWED):
        with open(REVIEWED, 'r', encoding='utf-8') as rf, open(DATASET, 'a', encoding='utf-8') as df:
            for line in rf:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                case = obj.get('caseText','').strip()
                if not case or case in existing:
                    continue
                df.write(json.dumps(obj, ensure_ascii=False) + '\n')
                existing.add(case)
                merged += 1
    print(f'Merged {merged} reviewed entries into {DATASET}')

    print('Retraining classifier now...')
    runpy.run_path(os.path.join(ROOT, 'backend', 'retrain_classifier.py'), run_name='__main__')
    print('Retraining complete.')

def main():
    print('Labeling pipeline starting.')
    run_auto_label()
    run_reviewer()
    merge_reviewed_and_retrain()
    print('Pipeline finished. Check backend/dataset.jsonl and backend/model_retrained.joblib')

if __name__ == '__main__':
    main()
