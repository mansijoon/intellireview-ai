from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Iterable

import numpy as np
from dotenv import load_dotenv
from google import genai


EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSIONS = 3072
CACHE_VERSION = "semantic-rag-v1"


class EmbeddingService:
    """Gemini embedding service with a local content-addressed cache."""

    def __init__(
        self,
        cache_root: str | Path = ".intellireview-cache",
    ) -> None:
        load_dotenv(
            dotenv_path=Path.cwd() / ".env"
        )

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is required for semantic retrieval"
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.cache_root = (
            Path(cache_root).resolve()
            / "embeddings"
        )

        self.cache_root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _cache_key(
        self,
        text: str,
        *,
        task_type: str,
    ) -> str:
        digest = hashlib.sha256()

        digest.update(
            CACHE_VERSION.encode("utf-8")
        )
        digest.update(b"\0")
        digest.update(
            EMBEDDING_MODEL.encode("utf-8")
        )
        digest.update(b"\0")
        digest.update(
            task_type.encode("utf-8")
        )
        digest.update(b"\0")
        digest.update(
            text.encode("utf-8")
        )

        return digest.hexdigest()

    def _cache_path(
        self,
        key: str,
    ) -> Path:
        return (
            self.cache_root
            / f"{key}.json"
        )

    def _load_cached(
        self,
        key: str,
    ) -> list[float] | None:
        path = self._cache_path(key)

        if not path.exists():
            return None

        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

            embedding = payload["embedding"]

            if (
                not isinstance(
                    embedding,
                    list,
                )
                or len(embedding)
                != EMBEDDING_DIMENSIONS
            ):
                return None

            return [
                float(value)
                for value in embedding
            ]

        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            json.JSONDecodeError,
        ):
            return None

    def _save_cached(
        self,
        key: str,
        embedding: list[float],
    ) -> None:
        path = self._cache_path(key)
        temporary = path.with_suffix(
            ".tmp"
        )

        payload = {
            "model": EMBEDDING_MODEL,
            "dimensions": EMBEDDING_DIMENSIONS,
            "embedding": embedding,
        }

        try:
            temporary.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            temporary.replace(path)

        finally:
            if temporary.exists():
                temporary.unlink(
                    missing_ok=True
                )

    def embed(
        self,
        text: str,
        *,
        task_type: str = "RETRIEVAL_DOCUMENT",
    ) -> list[float]:
        key = self._cache_key(
            text,
            task_type=task_type,
        )

        cached = self._load_cached(key)

        if cached is not None:
            return cached

        result = self.client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config={
                "task_type": task_type,
                "output_dimensionality": EMBEDDING_DIMENSIONS,
            },
        )

        embedding = result.embeddings[0].values

        if len(embedding) != EMBEDDING_DIMENSIONS:
            raise RuntimeError(
                "Unexpected Gemini embedding dimensions: "
                f"{len(embedding)}"
            )

        embedding = [
            float(value)
            for value in embedding
        ]

        self._save_cached(
            key,
            embedding,
        )

        return embedding

    def embed_many(
        self,
        texts: Iterable[str],
        *,
        task_type: str = "RETRIEVAL_DOCUMENT",
    ) -> list[list[float]]:
        """
        Embed multiple texts using Gemini's batch content API.

        Cached items are returned from the local cache. Only cache misses
        are sent to Gemini.
        """

        text_list = list(texts)

        if not text_list:
            return []

        results: list[list[float] | None] = [
            None
            for _ in text_list
        ]

        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        for index, text in enumerate(
            text_list
        ):
            key = self._cache_key(
                text,
                task_type=task_type,
            )

            cached = self._load_cached(
                key
            )

            if cached is not None:
                results[index] = cached
            else:
                uncached_indices.append(
                    index
                )
                uncached_texts.append(
                    text
                )

        if uncached_texts:
            response = self.client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=uncached_texts,
                config={
                    "task_type": task_type,
                    "output_dimensionality": EMBEDDING_DIMENSIONS,
                },
            )

            embeddings = [
                embedding.values
                for embedding in response.embeddings
            ]

            if len(embeddings) != len(
                uncached_texts
            ):
                raise RuntimeError(
                    "Gemini returned an unexpected "
                    "number of embeddings: "
                    f"{len(embeddings)} != "
                    f"{len(uncached_texts)}"
                )

            for index, text, embedding in zip(
                uncached_indices,
                uncached_texts,
                embeddings,
            ):
                if len(embedding) != (
                    EMBEDDING_DIMENSIONS
                ):
                    raise RuntimeError(
                        "Unexpected Gemini embedding "
                        "dimensions: "
                        f"{len(embedding)}"
                    )

                normalized = [
                    float(value)
                    for value in embedding
                ]

                results[index] = normalized

                key = self._cache_key(
                    text,
                    task_type=task_type,
                )

                self._save_cached(
                    key,
                    normalized,
                )

        if any(
            result is None
            for result in results
        ):
            raise RuntimeError(
                "Embedding batch contains missing results"
            )

        return [
            result
            for result in results
            if result is not None
        ]

    def embed_query(
        self,
        query: str,
    ) -> list[float]:
        return self.embed(
            query,
            task_type="RETRIEVAL_QUERY",
        )


def cosine_similarity(
    left: Iterable[float],
    right: Iterable[float],
) -> float:
    left_array = np.asarray(
        list(left),
        dtype=np.float32,
    )

    right_array = np.asarray(
        list(right),
        dtype=np.float32,
    )

    left_norm = np.linalg.norm(
        left_array
    )

    right_norm = np.linalg.norm(
        right_array
    )

    if (
        left_norm == 0
        or right_norm == 0
    ):
        return 0.0

    return float(
        np.dot(
            left_array,
            right_array,
        )
        / (
            left_norm
            * right_norm
        )
    )
