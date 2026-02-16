"""
文本向量化服务：封装 sentence-transformers
"""
from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from config import Config


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    懒加载嵌入模型，避免重复加载
    """
    model_name = Config.EMBEDDING_MODEL
    return SentenceTransformer(model_name)


def encode_text(text: str) -> List[float]:
    """
    将单条文本编码为向量（list[float]）
    """
    model = get_embedding_model()
    emb = model.encode([text])[0]
    return emb.tolist()


def encode_texts(texts: List[str]) -> List[List[float]]:
    """
    将多条文本编码为向量列表
    """
    model = get_embedding_model()
    embs = model.encode(texts)
    return [e.tolist() for e in embs]

