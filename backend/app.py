
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json
import joblib
import os as _os
import logging
import datetime
import json as _json

# Optional semantic (embedding) classifier for free, local inference
try:
    from . import emb_classifier
except Exception:
    try:
        import emb_classifier
    except Exception:
        emb_classifier = None

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'backend/uploads'
HISTORY_FILE = 'backend/history.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MODEL_FILE = 'backend/model.joblib'
classifier = None
classifier_threshold = float(_os.environ.get('CLASSIFIER_THRESHOLD', 0.6))
emb_threshold = float(_os.environ.get('EMB_THRESHOLD', 0.35))
# mapping from classifier labels to suggestion bundles
CLASSIFIER_MAPS = {
    'theft': {
        'category': 'Theft',
        'laws': [
            {'code': 'IPC 378', 'desc': 'Theft'},
            {'code': 'IPC 379', 'desc': 'Punishment for theft'},
            {'code': 'IPC 380', 'desc': 'Theft in dwelling house'},
            {'code': 'IPC 457', 'desc': 'House-trespass or house-breaking'}
        ],
        'defenses': ['Mistaken identity', 'Alibi', 'Insufficient evidence'],
        'reasons': {
            'IPC 378': 'Property taken without consent (theft).',
            'IPC 379': 'Punishment section applicable when theft is established.',
            'IPC 380': 'Applicable when theft occurred in a dwelling/house.',
            'IPC 457': 'House-trespass or housebreaking to commit theft.'
        },
        'followUps': [
            'Was there forced entry or signs of breaking in (yes/no)?',
            'Was anything else damaged or stolen (brief)?',
            'Do you suspect someone who had access (domestic helper/guest) (yes/no)?',
            'Approximate value of stolen items (low/medium/high)?'
        ]
    },
    'murder': {
        'category': 'Homicide',
        'laws': [
            {'code': 'IPC 302', 'desc': 'Murder'},
            {'code': 'IPC 300', 'desc': 'Definition of Murder / Culpable Homicide'},
            {'code': 'IPC 304', 'desc': 'Culpable Homicide not amounting to Murder'},
            {'code': 'IPC 307', 'desc': 'Attempt to murder'}
        ],
        'defenses': ['Lack of intent / accidental', 'Self-defence', 'Sudden fight / provocation', 'Insanity / mental unsoundness'],
        'reasons': {
            'IPC 302': 'Death caused with intent or knowledge; primary section for killing.',
            'IPC 300': 'Check whether elements amount to murder; helps decide between 302 and 304.',
            'IPC 304': 'When mens rea for murder is absent or reduced.',
            'IPC 307': 'If victim survived or there was an attempted killing.'
        },
        'followUps': [
            'Was there an intention to cause death (yes/no)?',
            'Was a weapon used? If yes, what?',
            'Were there multiple assailants (yes/no)?',
            'Was there any provocation or self-defence claimed (brief)?'
        ]
    },
    'cheating': {
        'category': 'Fraud',
        'laws': [
            {'code': 'IPC 420', 'desc': 'Cheating'},
            {'code': 'IPC 406', 'desc': 'Criminal Breach of Trust'},
            {'code': 'IPC 468', 'desc': 'Forgery'}
        ],
        'defenses': ['Lack of intention', 'Insufficient evidence', 'False accusation'],
        'reasons': {'IPC 420': 'Matched keyword: cheating/fraud'},
        'followUps': []
    },
    'defamation': {
        'category': 'Defamation',
        'laws': [{'code': 'IPC 500', 'desc': 'Defamation'}],
        'defenses': ['Truth as defense', 'Privilege', 'Fair comment'],
        'reasons': {'IPC 500': 'Matched defamation patterns.'},
        'followUps': []
    },
    'cybercrime': {
        'category': 'Cybercrime',
        'laws': [
            {'code': 'IT Act Section 66', 'desc': 'Computer-related offences / unauthorized access'},
            {'code': 'IT Act Section 66C', 'desc': 'Identity theft / fraud (as applicable)'}
        ],
        'defenses': ['Compromised credentials', 'SIM swap / phishing', 'Account takeover via third party'],
        'reasons': {'IT Act Section 66': 'Unauthorized access or hacking reported.'},
        'followUps': [
            'Was there any suspicious link or message (yes/no)?',
            'Approximate loss (none/low/medium/high)?',
            'Was MFA enabled (yes/no)?'
        ]
    },
    'impersonation': {
        'category': 'Cybercrime',
        'laws': [
            {'code': 'IT Act Section 66', 'desc': 'Unauthorized access / misuse of data'},
            {'code': 'IT Act Section 66C', 'desc': 'Identity theft / cheating by impersonation'},
            {'code': 'IPC 499/500', 'desc': 'Defamation (if false statements made under the profile)'}
        ],
        'defenses': ['Photos were publicly available or previously shared', 'Consent to use images', 'Mistaken identity'],
        'reasons': {
            'IT Act Section 66': 'Profile created using another person\'s images/personal data indicates misuse of digital identity.',
            'IT Act Section 66C': 'Impersonation or identity theft-like behavior reported.'
        },
        'followUps': [
            'Which platform is the fake profile on?',
            'Do you have screenshots or profile links (yes/no)?',
            'Was the profile used to contact others or request money (yes/no)?',
            'Any financial loss or reputational harm observed (brief)?'
        ]
    },
    'assault': {
        'category': 'Assault',
        'laws': [
            {'code': 'IPC 323', 'desc': 'Punishment for voluntarily causing hurt'},
            {'code': 'IPC 352', 'desc': 'Assault or criminal force'}
        ],
        'defenses': ['Self-defence', 'Provocation'],
        'reasons': {'IPC 323': 'Physical assault causing hurt.'},
        'followUps': ['Any medical records or photos of injuries (yes/no)?', 'Was the police informed (yes/no)?']
    },
    'domestic_violence': {
        'category': 'Domestic Violence',
        'laws': [
            {'code': 'IPC 498A', 'desc': 'Cruelty by husband or relatives'},
            {'code': 'Protection of Women from Domestic Violence Act', 'desc': 'Civil remedy for domestic violence'}
        ],
        'defenses': ['False accusation', 'Contextual disputes'],
        'reasons': {'IPC 498A': 'Allegations of cruelty and harassment within marriage.'},
        'followUps': ['Any medical records or police complaints (yes/no)?', 'Is there ongoing threat (yes/no)?']
    },
    'kidnapping': {
        'category': 'Kidnapping',
        'laws': [
            {'code': 'IPC 363', 'desc': 'Kidnapping'},
            {'code': 'IPC 364', 'desc': 'Kidnapping or abducting with intent to murder'}
        ],
        'defenses': ['Permission disputed', 'Mistaken identity'],
        'reasons': {'IPC 363': 'Removal of a person without consent indicates kidnapping.'},
        'followUps': ['Age of victim?', 'Any witnesses or CCTV?']
    },
    'sexual_harassment': {
        'category': 'Sexual Harassment',
        'laws': [{'code': 'POSH Act / IPC 354A', 'desc': 'Sexual harassment at workplace / molestation'}],
        'defenses': ['Consensual interaction disputed', 'False complaint'],
        'reasons': {'POSH Act / IPC 354A': 'Workplace sexual harassment allegations; internal POSH mechanism and criminal remedies may apply.'},
        'followUps': ['Any messages/screenshots available (yes/no)?', 'Was it reported to HR (yes/no)?']
    },
    'drug_offence': {
        'category': 'Drug Offence',
        'laws': [{'code': 'NDPS', 'desc': 'Narcotic Drugs and Psychotropic Substances Act'}],
        'defenses': ['Lack of possession', 'Unlawful search'],
        'reasons': {'NDPS': 'Possession or trafficking of controlled substances under NDPS Act.'},
        'followUps': ['Quantity and type of substance?', 'Chain of custody for evidence?']
    },
    'traffic_offence': {
        'category': 'Traffic Offence',
        'laws': [{'code': 'IPC 304A', 'desc': 'Causing death by negligence'}, {'code': 'Motor Vehicles Act', 'desc': 'Traffic offences and penalties'}],
        'defenses': ['No intoxication claim', 'Mechanical failure'],
        'reasons': {'IPC 304A': 'Negligent driving causing harm; check for intoxication or reckless behaviour.'},
        'followUps': ['Was the driver tested for alcohol (yes/no)?', 'Police FIR filed (yes/no)?']
    },
    'medical_negligence': {
        'category': 'Medical Negligence',
        'laws': [{'code': 'IPC 304A', 'desc': 'Causing death by negligence (if death occurred)'}, {'code': 'Medical Negligence - Civil', 'desc': 'Civil claim for damages and professional negligence'}],
        'defenses': ['Informed consent claimed', 'Unforeseen complication'],
        'reasons': {'Medical Negligence - Civil': 'Medical negligence claim; civil remedies may apply; criminal negligence possible depending on harm.'},
        'followUps': ['Medical records available (yes/no)?', 'Any expert opinion obtained (yes/no)?']
    },
    'extortion': {
        'category': 'Extortion',
        'laws': [
            {'code': 'IPC 383', 'desc': 'Extortion'},
            {'code': 'IPC 387', 'desc': 'Putting a person in fear to commit extortion'}
        ],
        'defenses': ['False allegation', 'Mistaken identity'],
        'reasons': {'IPC 383': 'Threats combined with demand for money indicate extortion.'},
        'followUps': [
            'Do you have call recordings (yes/no)?',
            'Amount demanded?',
            'Any threats to life or family (yes/no)?'
        ]
    },
    'Labour/Employment': {
        'category': 'Labour/Employment',
        'laws': [{'code': 'Labour law remedy', 'desc': 'Wrongful termination / reinstatement / compensation'}],
        'defenses': ['Wrongful termination', 'Retaliation claims'],
        'reasons': {'Labour law remedy': 'Employment and administrative remedies may apply.'},
        'followUps': ['Any written complaints filed (yes/no)?', 'HR correspondence available (yes/no)?']
    },
    'Civil': {
        'category': 'Civil',
        'laws': [{'code': 'Civil remedy', 'desc': 'Civil claim / damages / injunctions'}],
        'defenses': ['Lack of cause', 'Title dispute (for property)'],
        'reasons': {'Civil remedy': 'Civil action recommended; specific remedy depends on facts.'},
        'followUps': ['Do you have documents or title deeds (yes/no)?']
    },
    'Criminal': {
        'category': 'Criminal',
        'laws': [{'code': 'Review facts', 'desc': 'Classifier indicates criminal matter; check detailed mapping or use embeddings for specifics.'}],
        'defenses': ['Depends on offence'],
        'reasons': {'Review facts': 'Classifier returned a broad criminal label; more context required to map to specific IPC sections.'},
        'followUps': []
    },
    'Corruption': {
        'category': 'Corruption',
        'laws': [{'code': 'IPC 171D', 'desc': 'Bribery / corruption related offences (context-specific)'}],
        'defenses': ['Lack of direct evidence'],
        'reasons': {'IPC 171D': 'Allegations of bribery/corruption may require administrative and criminal review.'},
        'followUps': ['Any documents or whistleblower reports (yes/no)?']
    },
    'Negligence': {
        'category': 'Negligence',
        'laws': [{'code': 'IPC 304A', 'desc': 'Causing death by negligence (if death)'}, {'code': 'Civil - negligence', 'desc': 'Civil claim for damages'}],
        'defenses': ['Standard of care dispute', 'Unforeseen complications'],
        'reasons': {'IPC 304A': 'Negligent act causing harm; civil and sometimes criminal remedies apply.'},
        'followUps': ['Medical records available (yes/no)?', 'Expert opinion obtained (yes/no)?']
    }
}

if os.path.exists(MODEL_FILE):
    try:
        classifier = joblib.load(MODEL_FILE)
        print('Classifier loaded from', MODEL_FILE)
    except Exception as e:
        print('Failed to load classifier:', e)

# Setup structured logging
LOG_DIR = 'backend/logs'
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'analysis.log')
logger = logging.getLogger('analysis_logger')
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

def log_analysis(entry: dict):
    try:
        entry['timestamp'] = datetime.datetime.utcnow().isoformat() + 'Z'
        logger.info(_json.dumps(entry, ensure_ascii=False))
    except Exception as e:
        print('Failed to write log entry:', e)

# LLM integrations removed — this project runs in free/offline mode using local classifier and embeddings.

# Load or initialize history
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'w') as f:
        json.dump([], f)

def load_history():
    with open(HISTORY_FILE, 'r') as f:
        data = json.load(f)
        # ensure legacy entries have 'viewed' flag
        for item in data:
            if 'viewed' not in item:
                item['viewed'] = False
        return data

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

@app.route('/analyze', methods=['POST'])
def analyze():
    case_text = request.form.get('caseText', '').strip()
    files = request.files.getlist('files')
    # Validation: require case description
    if not case_text:
        return jsonify({'error': 'Case description is required.'}), 400
    # Optional: limit file size (5MB per file)
    for file in files:
        if file and file.content_length and file.content_length > 5 * 1024 * 1024:
            return jsonify({'error': 'Each file must be less than 5MB.'}), 400
    saved_files = []
    for file in files:
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            saved_files.append(filename)
    # Simple keyword-based mapping (replace with real NLP/ML later)
    text_lower = case_text.lower()
    laws = []
    defenses = []
    category = 'Uncategorized'
    reasons = {}
    follow_ups = []

    # LLM disabled — offline-only pipeline
    used_llm = False
    llm_result = None

    # If LLM not used/failed, try classifier
    used_classifier = False
    classifier_info = None
    if not used_llm and classifier is not None:
        try:
            probs = classifier.predict_proba([case_text])[0]
            top_idx = int(probs.argmax())
            top_label = classifier.classes_[top_idx]
            top_conf = float(probs[top_idx])
            classifier_info = {'label': top_label, 'confidence': top_conf}
            if top_conf >= classifier_threshold:
                if top_label in CLASSIFIER_MAPS:
                    mapping = CLASSIFIER_MAPS[top_label]
                    category = mapping['category']
                    laws = mapping['laws']
                    defenses = mapping['defenses']
                    reasons = mapping['reasons']
                    follow_ups = mapping.get('followUps', [])
                    used_classifier = True
                else:
                    # label unknown to maps; still mark classifier used but keep category
                    used_classifier = True
        except Exception as e:
            print('Classifier prediction failed:', e)

    # Post-classifier keyword override: if classifier produced a broad criminal label
    # but the text clearly indicates impersonation/fake-profile, prefer the
    # `impersonation` mapping so users get concrete follow-ups/laws.
    if not used_llm and used_classifier and any(k in text_lower for k in ['fake profile', 'fake account', 'impersonat', 'using my photos', 'using my pictures', 'created a fake profile']):
        if 'impersonation' in CLASSIFIER_MAPS:
            mapping = CLASSIFIER_MAPS['impersonation']
            category = mapping['category']
            laws = mapping['laws']
            defenses = mapping['defenses']
            reasons = mapping['reasons']
            follow_ups = mapping.get('followUps', [])

    # Semantic embedding fallback (free) if available and no LLM/classifier used
    used_semantic = False
    semantic_info = None
    if not used_llm and not used_classifier and emb_classifier is not None:
        try:
            sem = emb_classifier.predict(case_text)
            # sem['dists'] are cosine distances; lower is more similar
            if sem and 'dists' in sem and len(sem['dists']) > 0:
                best_dist = float(sem['dists'][0])
                cand_labels = sem.get('labels', [])
                # pick top candidate label
                top_label = cand_labels[0] if cand_labels else None
                semantic_info = {'labels': cand_labels, 'dists': sem.get('dists'), 'examples': sem.get('examples')}
                if top_label and best_dist <= emb_threshold:
                    if top_label in CLASSIFIER_MAPS:
                        mapping = CLASSIFIER_MAPS[top_label]
                        category = mapping['category']
                        laws = mapping['laws']
                        defenses = mapping['defenses']
                        reasons = mapping['reasons']
                        follow_ups = mapping.get('followUps', [])
                        used_semantic = True
        except Exception as e:
            print('Semantic predictor failed:', e)

    if not used_llm and not used_classifier and not used_semantic and any(k in text_lower for k in ['kill', 'killed', 'murder', 'stabbed', 'shot', 'hacked to death', 'slain']):
        category = 'Criminal'
        laws = [
            {'code': 'IPC 302', 'desc': 'Murder'},
            {'code': 'IPC 300', 'desc': 'Definition of Murder / Culpable Homicide'},
            {'code': 'IPC 304', 'desc': 'Culpable Homicide not amounting to Murder'},
            {'code': 'IPC 307', 'desc': 'Attempt to murder'}
        ]
        defenses = ['Lack of intent / accidental', 'Self-defence', 'Sudden fight / provocation', 'Insanity / mental unsoundness']
        reasons = {
            'IPC 302': 'Used when death was caused with intent or knowledge; primary section for killing.',
            'IPC 300': 'Check whether elements amount to murder; helps decide between 302 and 304.',
            'IPC 304': 'Used when death resulted but mens rea for murder is absent or reduced.',
            'IPC 307': 'If the victim survived or there was an attempt to kill.'
        }
        follow_ups = [
            'Was there an intention to cause death (yes/no)?',
            'Was a weapon used? If yes, what?',
            'Were there multiple assailants (yes/no)?',
            'Was there any provocation or self-defence claimed (brief)?'
        ]
    # Impersonation / fake profile detection
    elif not used_llm and not used_classifier and not used_semantic and any(k in text_lower for k in ['fake profile', 'fake account', 'impersonat', 'using my photos', 'using my pictures', 'created a fake profile']):
        mapping = CLASSIFIER_MAPS.get('impersonation')
        if mapping:
            category = mapping['category']
            laws = mapping['laws']
            defenses = mapping['defenses']
            reasons = mapping['reasons']
            follow_ups = mapping.get('followUps', [])
            used_classifier = True
    # Cybercrime / unauthorized access detection (bank hacks, account takeover)
    elif not used_llm and not used_classifier and not used_semantic and any(k in text_lower for k in ['hack', 'hacked', 'hacking', 'bank account', 'unauthorized access', 'phishing', 'password', 'account hacked', 'upi', 'transfered', 'transferred']):
        category = 'Cybercrime'
        laws = [
            {'code': 'IT Act Section 66', 'desc': 'Unauthorized access / hacking'},
            {'code': 'IT Act Section 66C', 'desc': 'Identity theft / fraud (if applicable)'}
        ]
        defenses = ['Compromised credentials', 'Phishing / SIM swap', 'Third-party access']
        reasons = {
            'IT Act Section 66': 'The description indicates unauthorized access to an online account or service.'
        }
        follow_ups = [
            'Was there any suspicious message or link (yes/no)?',
            'Was there an unauthorized transfer (yes/no)?',
            'Approximate amount taken (none/low/medium/high)?'
        ]
    # Theft / burglary / robbery detection
    elif not used_llm and not used_classifier and any(k in text_lower for k in ['steal', 'stolen', 'stole', 'theft', 'robbed', 'robbery', 'burglary', 'break in', 'break-in', 'housebreaking', 'missing', 'gold', 'jewellery', 'jewelry', 'silver']):
        category = 'Criminal'
        laws = [
            {'code': 'IPC 378', 'desc': 'Theft'},
            {'code': 'IPC 379', 'desc': 'Punishment for theft'},
            {'code': 'IPC 380', 'desc': 'Theft in dwelling house'},
            {'code': 'IPC 457', 'desc': 'House-trespass or house-breaking'}
        ]
        defenses = ['Mistaken identity', 'Alibi', 'Insufficient evidence']
        reasons = {
            'IPC 378': 'The description indicates property was taken without consent (theft).',
            'IPC 379': 'Punishment section applicable when theft is established.',
            'IPC 380': 'If theft occurred in a dwelling/house (owner absent), this may apply.',
            'IPC 457': 'If there was house-trespass or housebreaking to commit theft.'
        }
        follow_ups = [
            'Was there forced entry or signs of breaking in (yes/no)?',
            'Was anything else damaged or stolen (brief)?',
            'Do you suspect someone who had access (domestic helper/guest) (yes/no)?',
            'Approximate value of stolen items (low/medium/high)?'
        ]
    elif not used_llm and not used_classifier and 'cheating' in text_lower:
        category = 'Criminal'
        laws = [
            {'code': 'IPC 420', 'desc': 'Cheating'},
            {'code': 'IPC 406', 'desc': 'Criminal Breach of Trust'},
            {'code': 'IPC 468', 'desc': 'Forgery'}
        ]
        defenses = ['Lack of intention', 'Insufficient evidence', 'False accusation']
        reasons = {l['code']: 'Matched keyword: cheating/fraud' for l in laws}
    # Extortion / blackmail detection
    elif not used_llm and not used_classifier and not used_semantic and any(k in text_lower for k in ['threatened', 'threat', 'blackmail', 'extortion', 'demanded money', 'ransom']):
        category = 'Criminal'
        laws = [
            {'code': 'IPC 383', 'desc': 'Extortion'},
            {'code': 'IPC 387', 'desc': 'Putting in fear of death or grievous hurt, extortion'}
        ]
        defenses = ['False allegation', 'Mistaken identity']
        reasons = {
            'IPC 383': 'Threats coupled with demand for money indicate extortion.'
        }
        follow_ups = [
            'Do you have call recordings (yes/no)?',
            'Amount demanded?',
            'Any threats to life or family (yes/no)?'
        ]
    elif not used_llm and not used_classifier:
        # fallback default
        category = 'Civil'
        laws = [{'code': 'IPC 500', 'desc': 'Defamation'}]
        defenses = ['Truth as defense', 'Privilege', 'Fair comment']
        reasons = {'IPC 500': 'Matched default civil mapping.'}
    else:
        # classifier provided the mapping
        pass
    # Accept structured follow-up answers if provided
    follow_up_answers = None
    if 'followUpAnswers' in request.form:
        try:
            follow_up_answers = json.loads(request.form.get('followUpAnswers'))
        except Exception:
            follow_up_answers = None

    result = {
        'caseText': case_text,
        'files': saved_files,
        'category': category,
        'laws': laws,
        'defenses': defenses,
        'reasons': reasons,
        'followUps': follow_ups,
        'followUpAnswers': follow_up_answers
    }

    # Save to history with dedup/update rules:
    # - If an identical entry (by `caseText`) exists and has been viewed, do not add/move it
    # - If it exists but content changed, update the entry and move it to top (append)
    # - If it does not exist, append as new
    history = load_history()
    normalized = case_text.strip().lower()
    existing_idx = None
    for i, item in enumerate(history):
        if item.get('caseText', '').strip().lower() == normalized:
            existing_idx = i
            break

    def content_changed(old, new):
        # compare main fields that matter for 'update'
        keys = ['category', 'laws', 'defenses', 'reasons', 'followUpAnswers']
        for k in keys:
            if old.get(k) != new.get(k):
                return True
        return False

    if existing_idx is not None:
        existing = history[existing_idx]
        # ensure 'viewed' flag exists
        if 'viewed' not in existing:
            existing['viewed'] = False
        if existing['viewed'] and not content_changed(existing, result):
            # already viewed and no change — return existing without adding/moving
            result = existing
        else:
            # update fields and move to top (append)
            # preserve id and viewed reset to False
            preserved_id = existing.get('id')
            history.pop(existing_idx)
            result['id'] = preserved_id if preserved_id is not None else (len(history) + 1)
            result['viewed'] = False
            history.append(result)
            save_history(history)
    else:
        # new entry
        result['id'] = len(history) + 1
        result['viewed'] = False
        history.append(result)
        save_history(history)
    # Log analysis details (LLM/classifier/fallback info)
    log_entry = {
        'id': result['id'],
        'category': category,
        'used_llm': bool(used_llm),
        'llm_result_label': llm_result.get('category') if (used_llm and isinstance(llm_result, dict)) else None,
        'used_classifier': bool(used_classifier),
        'classifier_info': classifier_info,
        'used_semantic': bool(used_semantic),
        'semantic_info': semantic_info,
        'fallback_to_rules': (not used_llm and not used_classifier and not used_semantic),
        'classifier_threshold': classifier_threshold,
        'input_length': len(case_text),
        'files_count': len(saved_files)
    }
    log_analysis(log_entry)
    return jsonify(result)

@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(load_history())


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/history/<int:analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    history = load_history()
    history = [item for item in history if item['id'] != analysis_id]
    save_history(history)
    return jsonify({'success': True})


@app.route('/history/<int:analysis_id>/view', methods=['POST'])
def mark_viewed(analysis_id):
    history = load_history()
    changed = False
    for item in history:
        if item.get('id') == analysis_id:
            item['viewed'] = True
            changed = True
            break
    if changed:
        save_history(history)
        return jsonify({'success': True})
    return jsonify({'error': 'not found'}), 404

@app.route('/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
