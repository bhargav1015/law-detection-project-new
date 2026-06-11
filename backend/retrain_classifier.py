import json
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

DATA_FILE = 'backend/dataset.jsonl'
MODEL_FILE = 'backend/model_retrained.joblib'
META_FILE = 'backend/model_retrained_meta.json'


def load_dataset(path):
    X = []
    y = []
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            X.append(obj.get('caseText',''))
            # use category as label; for multi-label you'd adapt
            y.append(obj.get('category','Uncategorized'))
    return X, y


def train_and_save(X, y, model_path, meta_path):
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1,2), stop_words='english')),
        ('clf', LogisticRegression(max_iter=2000))
    ])

    unique_labels = sorted(set(y))
    if len(unique_labels) < 2:
        # Only one class present — save a DummyClassifier that predicts the constant label
        const_label = unique_labels[0]
        dummy = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1,2), stop_words='english')),
            ('clf', DummyClassifier(strategy='constant', constant=const_label))
        ])
        dummy.fit(X, y)
        joblib.dump(dummy, model_path)
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump({'classes': [const_label], 'note': 'Dummy classifier saved because only one label present'}, f)
        print('Only one label present; saved DummyClassifier to', model_path)
        return None

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)
    report = classification_report(y_test, preds, zero_division=0)
    print('Classification report:\n', report)
    joblib.dump(pipeline, model_path)
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump({'classes': pipeline.named_steps['clf'].classes_.tolist()}, f)
    print('Saved retrained model to', model_path)
    return report


if __name__ == '__main__':
    X, y = load_dataset(DATA_FILE)
    print(f'Loaded {len(X)} examples, {len(set(y))} labels: {sorted(set(y))}')
    train_and_save(X, y, MODEL_FILE, META_FILE)
