from __future__ import annotations

import hashlib
import uuid
from typing import Any, Dict, List, Sequence, Optional

import chromadb
from sentence_transformers import SentenceTransformer

class RAGKnowledgeBase:
    EMB_MODEL = "all-MiniLM-L6-v2"
    DEFAULT_COLLECTION = "transform_cache"

    def __init__(self, collection_name: str | None = None) -> None:
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(
            name=collection_name or self.DEFAULT_COLLECTION
        )
        self.model = SentenceTransformer(self.EMB_MODEL)
        print(f"RAG Knowledge Base initialized with collection: {self.collection.name}")
        print(f"Current cache entries: {self.collection.count()}")

    def _embed(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    def add_conversion(
        self,
        component_type: str,
        input_props: str,
        output_code: str,
        source: str = "auto_learned",
    ) -> None:
        if not component_type:
            component_type = "GenericComponent"
        unique_id = hashlib.md5(f"{component_type}:{input_props}".encode()).hexdigest()

        try:
            self.collection.delete(ids=[unique_id])
        except:
            pass

        try:
            self.collection.add(
                embeddings=[self._embed(output_code)],
                documents=[output_code],
                metadatas=[
                    {
                        "component_type": component_type,
                        "input_props": input_props,
                        "source": source,
                    }
                ],
                ids=[unique_id],
            )
        except Exception as e:
            print(f"Error adding to cache: {str(e)}")

    def query(
        self,
        query_text: str,
        *,
        n_results: int = 3,
        filters: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        try:
            where_filter = filters if filters else None
            res = self.collection.query(
                query_embeddings=[self._embed(query_text)],
                n_results=n_results,
                where=where_filter,
            )
            docs: Sequence[str] = res.get("documents", [[]])[0]
            results = []

            if docs:
                for i in range(len(docs)):
                    result = {
                        "text": docs[i],
                        "metadata": res["metadatas"][0][i] if "metadatas" in res and len(res["metadatas"]) > 0 else {},
                        "id": res["ids"][0][i] if "ids" in res and len(res["ids"]) > 0 else "",
                        "distance": res["distances"][0][i] if "distances" in res and len(res["distances"]) > 0 else None,
                    }
                    results.append(result)
            return results
        except Exception as e:
            print(f"Error querying knowledge base: {str(e)}")
            return []

    def best_match(self, component_type: str, props_str: str, *, threshold: float = 1.5) -> Dict[str, Any] | None:
        if not component_type:
            component_type = "GenericComponent"

        query = f"Code snippet for {component_type} with {props_str}"
        hits = self.query(query, n_results=1, filters={"component_type": component_type})

        if hits and hits[0]["distance"] < threshold:
            return hits[0]

        hits = self.query(query, n_results=1)
        if hits and hits[0]["distance"] < threshold:
            return hits[0]

        return None
