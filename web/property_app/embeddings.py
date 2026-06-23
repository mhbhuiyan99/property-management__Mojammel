from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_model():
    """
    Loads the sentence-transformers model once per process and reuses it.
    First call downloads the model (~90MB) from huggingface.co and caches
    it; subsequent calls (and subsequent container restarts, as long as
    the same volume/layer persists) are instant.
    """
    return SentenceTransformer(MODEL_NAME)


def generate_embedding(text):
    """Returns a 384-dim embedding (list of floats) for the given text."""
    model = get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()