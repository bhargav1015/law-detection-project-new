import json
import os

INPUT = 'backend/proposed_labels.jsonl'
OUT_REVIEWED = 'backend/dataset_reviewed.jsonl'

if not os.path.exists(INPUT):
    print('No proposals found at', INPUT)
    raise SystemExit(1)

print('Interactive review. Commands: (a)ccept, (e)dit, (s)kip, (q)uit')

with open(INPUT, 'r', encoding='utf-8') as inp, open(OUT_REVIEWED, 'a', encoding='utf-8') as out:
    for line in inp:
        obj = json.loads(line)
        case = obj.get('caseText')
        proposed = obj.get('proposed')
        print('\n---')
        print('Case:')
        print(case)
        print('\nProposed:')
        print(json.dumps(proposed, indent=2, ensure_ascii=False))
        while True:
            cmd = input('\nAction (a/e/s/q): ').strip().lower()
            if cmd == 'a':
                # accept as-is and append to reviewed dataset
                entry = {
                    'caseText': case,
                    'category': proposed.get('category','Uncategorized') if isinstance(proposed, dict) else 'Uncategorized',
                    'laws': proposed.get('laws',[]) if isinstance(proposed, dict) else [],
                    'defenses': proposed.get('defenses',[]) if isinstance(proposed, dict) else [],
                    'reasons': proposed.get('reasons',{}) if isinstance(proposed, dict) else {},
                    'followUps': proposed.get('followUps',[]) if isinstance(proposed, dict) else [],
                    'notes': 'accepted'
                }
                out.write(json.dumps(entry, ensure_ascii=False) + '\n')
                print('Accepted and saved to', OUT_REVIEWED)
                break
            elif cmd == 'e':
                print('Enter JSON for final entry (single-line). Example:')
                print('{"category":"Criminal","laws":[{"code":"IPC 378","desc":"Theft"}],"defenses":[],"reasons":{},"followUps":[]}')
                edit = input('Edited JSON: ').strip()
                try:
                    parsed = json.loads(edit)
                    entry = {
                        'caseText': case,
                        'category': parsed.get('category','Uncategorized'),
                        'laws': parsed.get('laws',[]),
                        'defenses': parsed.get('defenses',[]),
                        'reasons': parsed.get('reasons',{}),
                        'followUps': parsed.get('followUps',[]),
                        'notes': 'edited'
                    }
                    out.write(json.dumps(entry, ensure_ascii=False) + '\n')
                    print('Edited entry saved')
                    break
                except Exception as e:
                    print('Invalid JSON:', e)
                    continue
            elif cmd == 's':
                print('Skipped')
                break
            elif cmd == 'q':
                print('Quitting review')
                raise SystemExit(0)
            else:
                print('Unknown command')

print('Review complete. Reviewed entries appended to', OUT_REVIEWED)
