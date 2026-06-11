import json
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

DATA_FILE = 'backend/dataset.jsonl'

def load_dataset(path):
    X = []
    y = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    text = obj.get('caseText') or obj.get('text')
                    label = obj.get('category')
                    if text and label:
                        X.append(text)
                        y.append(label)
                except Exception:
                    continue
    else:
        # fallback: small built-in data
        X = [
            "Someone stole my gold when I was not at home",
            "He killed the victim with a knife",
            "He cheated me and took money by false promises",
            "She posted false statements about me online",
            "He assaulted me and I have injuries",
            "The accident occurred due to negligence",
            "My account was hacked and data stolen",
        ]
        y = ['theft', 'murder', 'cheating', 'defamation', 'assault', 'negligence', 'cybercrime']
    return X, y


X, y = load_dataset(DATA_FILE)

pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1,2), stop_words='english')),
    ('clf', LogisticRegression(max_iter=1000))
])

if len(X) < 2:
    raise SystemExit('Not enough training examples in dataset.')

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

pipeline.fit(X_train, y_train)

pred = pipeline.predict(X_test)
print(classification_report(y_test, pred))

# Save model
os.makedirs('backend', exist_ok=True)
joblib.dump(pipeline, 'backend/model.joblib')
print('Model saved to backend/model.joblib')

# Save labels (classes)
with open('backend/model_meta.json', 'w', encoding='utf-8') as f:
    json.dump({'classes': pipeline.named_steps['clf'].classes_.tolist()}, f)
print('Model metadata saved to backend/model_meta.json')
