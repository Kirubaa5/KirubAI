import math
import re
import hashlib
from abc import ABC, abstractmethod
from typing import List, Dict


class BaseEmbeddingProvider(ABC):
    """Abstract Base Class for text embedding generation."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate a normalized dense vector embedding for a text string."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vector embeddings for a list of text strings."""
        pass


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two vector lists."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    sim = dot_product / (norm_a * norm_b)
    # Clamp between 0.0 and 1.0 for positive space
    return max(0.0, min(1.0, float(sim)))


class DeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic dense vector embedding provider.
    Uses subword character n-grams and word tokens projected into a fixed-dimension
    vector space with L2 normalization.
    Provides fast, deterministic, reproducible embeddings without external network dependencies.
    """

    def __init__(self, dimension: int = 128):
        self.dimension = dimension

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r'[^a-zA-Z0-9\s\-]', ' ', text.lower())
        words = [w.strip() for w in cleaned.split() if len(w.strip()) > 1]
        tokens = list(words)

        # Add 3-gram and 4-gram character tokens for subword matching
        for word in words:
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    tokens.append(f"__3g_{word[i:i+3]}")
            if len(word) >= 4:
                for i in range(len(word) - 3):
                    tokens.append(f"__4g_{word[i:i+4]}")

        return tokens

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.dimension

        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self.dimension

        vector = [0.0] * self.dimension

        for token in tokens:
            # Deterministic hash to bucket
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            bucket = h % self.dimension
            # Sign hash for balanced projections
            sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
            # Higher weight for whole words vs subwords
            weight = 1.0 if not token.startswith("__") else 0.4
            vector[bucket] += sign * weight

        # L2 Normalization
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0.0:
            return [round(v / norm, 6) for v in vector]
        return [0.0] * self.dimension

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]
