from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    @property
    def embedding_size(self) -> int:
        return self.model.get_sentence_embedding_dimension()