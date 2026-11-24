from pathlib import Path
import joblib
import numpy as np

from ..data import normalize


class LexicalRetriever:
    def __init__(self, method="tfidf"):
        if method not in ("tfidf", "bm25"):
            raise ValueError(method)
        self.method = method

    def fit(self, products):
        docs = [normalize(p["text"]) for p in products]
        if self.method == "tfidf":
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=50000, sublinear_tf=True)
            self.matrix = self.vectorizer.fit_transform(docs)
        else:
            from rank_bm25 import BM25Okapi
            self.index = BM25Okapi([doc.split() for doc in docs])
        return self

    def score(self, query, indices):
        if not len(indices):
            return np.empty(0)
        query = normalize(query)
        if self.method == "tfidf":
            return (self.matrix[indices] @ self.vectorizer.transform([query]).T).toarray().ravel()
        return np.asarray(self.index.get_scores(query.split()))[indices]

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(path):
        # Only load artifacts produced by this project from trusted storage.
        return joblib.load(path)
