import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors

WORKDIR = os.path.dirname(__file__)
EMB_FILE = os.path.join(WORKDIR, 'embeddings.npz')
DS_FILE = os.path.join(WORKDIR, 'dataset.jsonl')
MODEL_NAME = os.environ.get('EMB_MODEL', 'all-MiniLM-L6-v2')


def build_embeddings(dataset_path=DS_FILE, model_name=MODEL_NAME, out_file=EMB_FILE):
    """Build and save embeddings + labels from dataset.jsonl."""
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(dataset_path)
    texts = []
    labels = []
    with open(dataset_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            texts.append(obj.get('caseText', ''))
            labels.append(obj.get('category', 'Uncategorized'))
    if not texts:
        raise ValueError('No texts found in dataset.jsonl')
    model = SentenceTransformer(model_name)
    embeds = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    np.savez(out_file, embeds=embeds, labels=np.array(labels, dtype=object), texts=np.array(texts, dtype=object))
    return out_file


def ensure_embeddings(dataset_path=DS_FILE, emb_file=EMB_FILE, model_name=MODEL_NAME):
    if not os.path.exists(emb_file):
        return build_embeddings(dataset_path, model_name, emb_file)
    return emb_file


def predict(case_text, emb_file=EMB_FILE, model_name=MODEL_NAME, k=3):
    """Return nearest labels, example texts and distances for the query.

    Result format: {'labels': [...], 'examples': [...], 'dists': [...]}
    """
    emb_file = ensure_embeddings()
    data = np.load(emb_file, allow_pickle=True)
    embeds = data['embeds']
    labels = data['labels']
    texts = data['texts']
    model = SentenceTransformer(model_name)
    q = model.encode([case_text], convert_to_numpy=True)
    nn = NearestNeighbors(n_neighbors=min(k, len(embeds)), metric='cosine')
    nn.fit(embeds)
    dists, idxs = nn.kneighbors(q)
    idxs = idxs[0].tolist()
    dists = dists[0].tolist()
    cand_labels = [labels[i] for i in idxs]
    cand_texts = [texts[i] for i in idxs]
    return {'labels': cand_labels, 'examples': cand_texts, 'dists': dists}


if __name__ == '__main__':
    # simple CLI to build embeddings
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--build', action='store_true')
    args = p.parse_args()
    if args.build:
        print('Building embeddings...')
        build_embeddings()
        print('Done')
