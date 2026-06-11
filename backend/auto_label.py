import os
import json
import re
import time
import requests

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'
PROMPT_VARIANT = os.environ.get('LLM_PROMPT_VARIANT', 'variant1')
INPUT_FILE = 'backend/unlabeled.jsonl'
OUTPUT_FILE = 'backend/proposed_labels.jsonl'

if not OPENAI_API_KEY:
    print('OPENAI_API_KEY not set. Set the environment variable and retry.')
    raise SystemExit(1)

if not os.path.exists(INPUT_FILE):
    print(f'No input file found at {INPUT_FILE}. Create one with one JSON per line containing {"caseText"}.')
    raise SystemExit(1)

# Build system/user prompts consistent with app.py variants
def build_prompt(case_text):
    base_system = (
        "You are a legal assistant. Return only a single JSON object with keys: category, laws (array of {code,desc}), "
        "defenses (array), reasons (object), followUps (array). Do not include extra text."
    )
    examples = (
        "Example case:\nSomeone broke into my house and stole jewellery.\nExample JSON:\n{"
        '"category"': '"Criminal"',
    )
    # For simplicity use a compact user prompt
    user_prompt = f"Now analyze this case and respond ONLY with valid JSON:\n{case_text}"
    return base_system, user_prompt

headers = {'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json'}

with open(INPUT_FILE, 'r', encoding='utf-8') as inp, open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
    for line in inp:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            case_text = obj.get('caseText') or obj.get('text') or obj.get('description')
            if not case_text:
                print('Skipping entry without caseText')
                continue
        except Exception:
            print('Skipping malformed JSON line')
            continue

        system_prompt, user_prompt = build_prompt(case_text)
        payload = {
            'model': 'gpt-4',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'max_tokens': 800,
            'temperature': 0.0
        }
        try:
            resp = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=30)
            if resp.status_code != 200:
                print('LLM error', resp.status_code, resp.text)
                time.sleep(1)
                continue
            j = resp.json()
            text = j['choices'][0]['message']['content']
            # extract JSON
            m = re.search(r'\{.*\}', text, re.S)
            json_text = m.group(0) if m else text
            try:
                parsed = json.loads(json_text)
            except Exception:
                parsed = {'_raw': text}

            proposed = {
                'caseText': case_text,
                'proposed': parsed,
                'raw': text
            }
            out.write(json.dumps(proposed, ensure_ascii=False) + '\n')
            print('Proposed label for:', case_text[:60])
            # be polite with rate limits
            time.sleep(1)
        except Exception as e:
            print('Request failed:', e)
            time.sleep(2)

print('Wrote proposals to', OUTPUT_FILE)
