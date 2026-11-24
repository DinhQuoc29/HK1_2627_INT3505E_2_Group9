from pathlib import Path
import joblib
from ..features import FEATURE_NAMES, FEATURE_VERSION


class SupervisedRanker:
    def __init__(self, model):
        self.model = model

    def predict(self, matrix):
        return self.model.predict(matrix)

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({'model': self.model, 'feature_names': FEATURE_NAMES,
                     'feature_version': FEATURE_VERSION}, path)

    @classmethod
    def load(cls, path):
        artifact = joblib.load(path)
        if artifact['feature_names'] != FEATURE_NAMES or artifact['feature_version'] != FEATURE_VERSION:
            raise ValueError('Feature schema/version mismatch')
        return cls(artifact['model'])
