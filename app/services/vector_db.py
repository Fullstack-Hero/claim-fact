from qdrant_client import QdrantClient, models
from typing import List, Dict, Optional
import os
import time
from dotenv import load_dotenv


load_dotenv()

class VectorDB:
    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = self._initialize_client()
        self.collection_name = "unified_collection"
        self._initialize_collection()

    def _initialize_client(self) -> QdrantClient:
        for attempt in range(self.max_retries):
            try:
                return QdrantClient(
                    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
                    api_key=os.getenv("QDRANT_API_KEY"),
                    timeout=10
                )
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Failed to connect to Qdrant after {self.max_retries} attempts: {str(e)}")
                time.sleep(self.retry_delay)

    def _initialize_collection(self, embedding_size: int = 384):
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            # Create collection without payload schema
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size,
                    distance=models.Distance.COSINE
                )
            )
        
        # Ensure index exists
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Create required indexes for filterable fields"""
        index_fields = [
            ("content_id", models.PayloadSchemaType.KEYWORD),
            ("type", models.PayloadSchemaType.KEYWORD),  # Add this line
        ]
        
        for field_name, schema_type in index_fields:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=schema_type
                )
                print(f"Created index for field: {field_name}")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"Index for {field_name} already exists")
                else:
                    print(f"Failed to create index for {field_name}: {str(e)}")

    def ensure_metadata_index(self, metadata_key: str):
        """Ensure index exists for a metadata field"""
        try:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name=f"metadata.{metadata_key}",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
        except Exception as e:
            if "already exists" not in str(e):
                print(f"Failed to create metadata index for {metadata_key}: {str(e)}")

    def add_items(self, points: List[models.PointStruct]):
        return self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def update_item(self, point_id: str, vector: List[float], payload: Dict):
        point = models.PointStruct(
            id=point_id,
            vector=vector,
            payload=payload
        )
        return self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

    def delete_item(self, point_id: str):
        return self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=[point_id])
        )

    def search(self, vector: List[float], filter: Optional[List[Dict]] = None, limit: int = 5):
        qdrant_filter = None
        if filter:
            # First ensure indexes exist for all filter fields
            for f in filter:
                if f["key"].startswith("metadata."):
                    metadata_key = f["key"].split(".", 1)[1]
                    self.ensure_metadata_index(metadata_key)
                    
            # Convert list of filter dicts to Qdrant Filter object
            conditions = []
            for f in filter:
                conditions.append(
                    models.FieldCondition(
                        key=f["key"],
                        match=models.MatchValue(value=f["match"]["value"])
                    )
                )
            qdrant_filter = models.Filter(must=conditions)
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            query_filter=qdrant_filter,
            limit=limit
        )

    def find_by_content_id(self, content_id: str):
        try:
            result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(
                        key="content_id",
                        match=models.MatchValue(value=content_id)
                    )]
                ),
                limit=1,
                with_vectors=True,
                with_payload=True
            )
            return result
        except Exception as e:
            raise ValueError(f"Error finding content_id {content_id}: {str(e)}")