from __future__ import annotations

import sys

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from analyzer.knowledge.documents import (
    build_knowledge_documents,
)
from analyzer.knowledge.embeddings import (
    EmbeddingService,
    cosine_similarity,
)
from analyzer.knowledge.models import (
    KnowledgeDocument,
    RepositoryKnowledgeModel,
)


@dataclass(frozen=True, slots=True)
class SemanticSearchResult:
    document: KnowledgeDocument
    score: float


class SemanticIndex:
    """
    Content-addressed semantic index for repository knowledge.

    Embeddings are cached by EmbeddingService, while this index stores
    the mapping between repository documents and their embedding vectors.
    """

    VERSION = "semantic-index-v1"

    def __init__(
        self,
        *,
        cache_root: str | Path = ".intellireview-cache",
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.cache_root = (
            Path(cache_root).resolve()
            / "semantic-index"
        )

        self.cache_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.embedding_service = (
            embedding_service
            or EmbeddingService(
                cache_root=cache_root,
            )
        )

        self.documents: tuple[
            KnowledgeDocument, ...
        ] = ()

        self.vectors: np.ndarray | None = None

    def _repository_key(
        self,
        knowledge: RepositoryKnowledgeModel,
    ) -> str:
        digest = hashlib.sha256()

        digest.update(
            self.VERSION.encode("utf-8")
        )
        digest.update(b"\0")
        digest.update(
            knowledge.repository_id.encode("utf-8")
        )
        digest.update(b"\0")
        digest.update(
            knowledge.revision.encode("utf-8")
        )

        return digest.hexdigest()

    def _index_path(
        self,
        knowledge: RepositoryKnowledgeModel,
    ) -> Path:
        return (
            self.cache_root
            / f"{self._repository_key(knowledge)}.json"
        )

    def load(
        self,
        knowledge: RepositoryKnowledgeModel,
    ) -> bool:
        """
        Load a persisted semantic index only when it exactly matches
        the current repository knowledge documents.
        """
        path = self._index_path(knowledge)

        if not path.exists():
            return False

        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

            if payload.get("version") != self.VERSION:
                return False

            if payload.get("repository_id") != (
                knowledge.repository_id
            ):
                return False

            if payload.get("revision") != (
                knowledge.revision
            ):
                return False

            raw_documents = payload.get(
                "documents"
            )

            raw_vectors = payload.get(
                "vectors"
            )

            if not isinstance(
                raw_documents,
                list,
            ):
                return False

            if not isinstance(
                raw_vectors,
                list,
            ):
                return False

            if len(raw_documents) != len(
                raw_vectors
            ):
                return False

            current_documents = (
                build_knowledge_documents(
                    knowledge
                )
            )

            if len(raw_documents) != len(
                current_documents
            ):
                return False

            for raw, current in zip(
                raw_documents,
                current_documents,
            ):
                if not isinstance(
                    raw,
                    dict,
                ):
                    return False

                if str(
                    raw.get("document_id")
                ) != current.document_id:
                    return False

                if str(
                    raw.get("kind")
                ) != current.kind:
                    return False

                if str(
                    raw.get("file_path")
                ) != current.file_path:
                    return False

                if str(
                    raw.get("name")
                ) != current.name:
                    return False

                if str(
                    raw.get("content")
                ) != current.content:
                    return False

                raw_line_start = raw.get(
                    "line_start"
                )

                raw_line_end = raw.get(
                    "line_end"
                )

                if (
                    raw_line_start
                    != current.line_start
                ):
                    return False

                if (
                    raw_line_end
                    != current.line_end
                ):
                    return False

            documents: list[
                KnowledgeDocument
            ] = []

            for raw in raw_documents:
                documents.append(
                    KnowledgeDocument(
                        document_id=str(
                            raw["document_id"]
                        ),
                        kind=str(
                            raw["kind"]
                        ),
                        file_path=str(
                            raw["file_path"]
                        ),
                        name=str(
                            raw["name"]
                        ),
                        content=str(
                            raw["content"]
                        ),
                        source_id=(
                            str(raw["source_id"])
                            if raw.get("source_id")
                            is not None
                            else None
                        ),
                        line_start=(
                            int(raw["line_start"])
                            if raw.get("line_start")
                            is not None
                            else None
                        ),
                        line_end=(
                            int(raw["line_end"])
                            if raw.get("line_end")
                            is not None
                            else None
                        ),
                    )
                )

            vectors = np.asarray(
                raw_vectors,
                dtype=np.float32,
            )

            if vectors.ndim != 2:
                return False

            if vectors.shape[0] != len(
                documents
            ):
                return False

            if vectors.shape[1] != 3072:
                return False

            self.documents = tuple(
                documents
            )

            self.vectors = vectors

            return True

        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            json.JSONDecodeError,
        ):
            return False

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> tuple[SemanticSearchResult, ...]:
        """
        Retrieve repository knowledge documents using semantic similarity.

        The query is embedded with RETRIEVAL_QUERY and compared against
        the persisted/build semantic document vectors.
        """
        if limit <= 0:
            return ()

        if not query.strip():
            return ()

        if self.vectors is None or not self.documents:
            return ()

        if self.vectors.ndim != 2:
            return ()

        if self.vectors.shape[0] != len(
            self.documents
        ):
            return ()

        query_vector = self.embedding_service.embed_query(
            query
        )

        if len(query_vector) != 3072:
            raise RuntimeError(
                "Unexpected query embedding dimensions: "
                f"{len(query_vector)}"
            )

        scored: list[SemanticSearchResult] = []

        for document, vector in zip(
            self.documents,
            self.vectors,
        ):
            score = cosine_similarity(
                query_vector,
                vector,
            )

            scored.append(
                SemanticSearchResult(
                    document=document,
                    score=score,
                )
            )

        scored.sort(
            key=lambda result: (
                -result.score,
                result.document.file_path,
                result.document.name,
                result.document.document_id,
            )
        )

        return tuple(
            scored[:limit]
        )

    def ensure(
        self,
        knowledge: RepositoryKnowledgeModel,
    ) -> bool:
        """
        Load a valid cached index or build and persist one.

        Returns True when a usable semantic index is available.
        """
        if self.load(knowledge):
            return True

        self.build(knowledge)

        return (
            self.vectors is not None
            and len(self.documents) > 0
        )

    def build(
        self,
        knowledge: RepositoryKnowledgeModel,
    ) -> None:
        documents = build_knowledge_documents(
            knowledge
        )

        if not documents:
            self.documents = ()
            self.vectors = np.empty(
                (0, 3072),
                dtype=np.float32,
            )
            return

        embedding_texts = [
            (
                f"kind: {document.kind}\n"
                f"name: {document.name}\n"
                f"path: {document.file_path}\n\n"
                f"{document.content}"
            )
            for document in documents
        ]

        batch_size = 10
        vectors: list[list[float]] = []
        start_index = 0

        partial = self._load_partial(
            knowledge,
            documents,
        )

        if partial is not None:
            start_index, vectors = partial

            print(
                f"Resuming semantic index at "
                f"document {start_index + 1}/"
                f"{len(documents)}",
                file=sys.stderr,
            )

        for start in range(
            start_index,
            len(embedding_texts),
            batch_size,
        ):
            batch = embedding_texts[
                start:start + batch_size
            ]

            end = min(
                start + batch_size,
                len(embedding_texts),
            )

            print(
                f"Embedding documents "
                f"{start + 1}-{end}/{len(documents)}",
                file=sys.stderr,
            )

            batch_vectors = (
                self.embedding_service.embed_many(
                    batch,
                    task_type="RETRIEVAL_DOCUMENT",
                )
            )

            if len(batch_vectors) != len(batch):
                raise RuntimeError(
                    "Embedding service returned an unexpected "
                    "number of vectors"
                )

            vectors.extend(batch_vectors)

            self.documents = tuple(
                documents[:end]
            )

            self.vectors = np.asarray(
                vectors,
                dtype=np.float32,
            )

            self._save(
                knowledge,
                complete=(
                    end == len(documents)
                ),
            )

        self.documents = tuple(
            documents
        )

        self.vectors = np.asarray(
            vectors,
            dtype=np.float32,
        )

    def _load_partial(
        self,
        knowledge: RepositoryKnowledgeModel,
        documents: tuple[KnowledgeDocument, ...],
    ) -> tuple[int, list[list[float]]] | None:
        path = self._index_path(knowledge)

        if not path.exists():
            return None

        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

            if payload.get("version") != self.VERSION:
                return None

            if payload.get("repository_id") != (
                knowledge.repository_id
            ):
                return None

            if payload.get("revision") != (
                knowledge.revision
            ):
                return None

            if payload.get("complete") is True:
                return None

            raw_documents = payload.get(
                "documents"
            )

            raw_vectors = payload.get(
                "vectors"
            )

            if not isinstance(
                raw_documents,
                list,
            ):
                return None

            if not isinstance(
                raw_vectors,
                list,
            ):
                return None

            count = len(raw_documents)

            if count == 0:
                return None

            if count > len(documents):
                return None

            if len(raw_vectors) != count:
                return None

            for raw, current in zip(
                raw_documents,
                documents[:count],
            ):
                if (
                    not isinstance(raw, dict)
                    or raw.get("document_id")
                    != current.document_id
                    or raw.get("kind")
                    != current.kind
                    or raw.get("file_path")
                    != current.file_path
                    or raw.get("name")
                    != current.name
                    or raw.get("content")
                    != current.content
                    or raw.get("line_start")
                    != current.line_start
                    or raw.get("line_end")
                    != current.line_end
                ):
                    return None

            vectors = np.asarray(
                raw_vectors,
                dtype=np.float32,
            )

            if vectors.ndim != 2:
                return None

            if vectors.shape != (
                count,
                3072,
            ):
                return None

            return (
                count,
                vectors.tolist(),
            )

        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            json.JSONDecodeError,
        ):
            return None

    def _save(
        self,
        knowledge: RepositoryKnowledgeModel,
        *,
        complete: bool = True,
    ) -> None:
        if self.vectors is None:
            raise RuntimeError(
                "Semantic index has not been built"
            )

        payload = {
            "version": self.VERSION,
            "repository_id": knowledge.repository_id,
            "revision": knowledge.revision,
            "complete": complete,
            "documents": [
                {
                    "document_id": document.document_id,
                    "kind": document.kind,
                    "source_id": document.source_id,
                    "file_path": document.file_path,
                    "name": document.name,
                    "content": document.content,
                    "line_start": document.line_start,
                    "line_end": document.line_end,
                }
                for document in self.documents
            ],
            "vectors": self.vectors.tolist(),
        }

        path = self._index_path(
            knowledge
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = path.with_suffix(
            ".tmp"
        )

        temporary.write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

        temporary.replace(path)

