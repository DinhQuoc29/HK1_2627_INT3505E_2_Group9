import hashlib
import json
from pathlib import Path
import numpy as np

from ..data import dump_json


class DenseRetriever:
    def __init__(self, method, model_id, device="cuda", batch_size=16, max_length=256, revision=None):
        self.method, self.model_id, self.device = method, model_id, device
        self.batch_size, self.max_length, self.revision = batch_size, max_length, revision
        self.encoder = None
        self.query_cache = {}
        self.resolved_revision = None

    def _encoder(self):
        if self.encoder is None:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer(self.model_id, revision=self.revision, device=self.device)
            self.encoder.max_seq_length = self.max_length
            config = self.encoder[0].auto_model.config
            self.resolved_revision = getattr(config, "_commit_hash", None) or self.revision
        return self.encoder

    def fit(self, products, cache_dir):
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        fingerprint = hashlib.sha256(json.dumps([(p["id"], p["text"]) for p in products], ensure_ascii=False).encode()).hexdigest()
        # Resolve the encoder revision even when reading cached vectors.
        encoder = self._encoder()
        identity = {"model_id": self.model_id, "revision": self.resolved_revision,
                    "max_length": self.max_length, "fingerprint": fingerprint, "method": self.method}
        metadata = cache_dir / 'index.json'
        vectors = cache_dir / 'vectors.npy'
        if metadata.exists() and vectors.exists() and json.loads(metadata.read_text()) == identity:
            self.vectors = np.load(vectors, mmap_mode="r")
        else:
            texts = [p["text"] for p in products]
            if self.method == "e5":
                texts = ["passage: " + text for text in texts]
            self.vectors = encoder.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                                          convert_to_numpy=True, show_progress_bar=True).astype("float32")
            np.save(vectors, self.vectors)
            dump_json(metadata, identity)
        if len(self.vectors) != len(products):
            raise ValueError("Embedding/catalog size mismatch")
        self.identity = identity
        return self

    def score(self, query, indices):
        if not len(indices):
            return np.empty(0)
        if query not in self.query_cache:
            text = "query: " + query if self.method == "e5" else query
            self.query_cache[query] = self._encoder().encode([text], normalize_embeddings=True,
                                                           convert_to_numpy=True)[0].astype("float32")
        return np.asarray(self.vectors[indices] @ self.query_cache[query])

    def clear_query_cache(self):
        self.query_cache.clear()
