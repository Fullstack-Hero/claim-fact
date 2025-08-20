from fastapi import APIRouter, HTTPException
from qdrant_client import QdrantClient, models
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import ContentItem, AddResponse, UpdateRequest, SearchQuery
from app.services.vector_db import VectorDB
from app.services.embedding import EmbeddingService
from app.utils.helpers import generate_content_id, generate_point_id, create_payload

router = APIRouter()
vector_db = VectorDB()
embedding_service = EmbeddingService()

@router.post("/add/", response_model=List[AddResponse])
async def add_items(items: List[ContentItem]):
    points = []
    responses = []
    
    for item in items:
        try:
            content_id = generate_content_id()
            embedding = embedding_service.generate_embedding(item.text)
            payload = create_payload(item, content_id)
            
            point_id = generate_point_id()
            point = models.PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            points.append(point)
            
            responses.append(AddResponse(
                id=point_id,
                content_id=content_id,
                type=item.type,
                metadata=item.metadata
            ))
        except Exception as e:
            print("exception: ", str(e))
            continue
    
    if points:
        vector_db.add_items(points)
        return responses
    raise HTTPException(status_code=400, detail="No items were added")


@router.post("/update/", status_code=status.HTTP_200_OK)
async def update_item(update_request: UpdateRequest):
    """
    Update or remove an item in the vector database
    
    Args:
        update_request: UpdateRequest with content_id and update parameters
    
    Returns:
        dict: Operation result with status and details
    """
    try:
        try:
            # Find the existing item by content_id
            search_result = vector_db.find_by_content_id(update_request.content_id)
        except ValueError as e:
            if "index" in str(e).lower():
                # If it's an index error, try to create the index
                vector_db._ensure_indexes()
                search_result = vector_db.find_by_content_id(update_request.content_id)
            else:
                raise
        if not search_result or not search_result[0]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with content_id {update_request.content_id} not found"
            )

        existing_point = search_result[0][0]

        if update_request.remove:
            # Delete the item
            vector_db.delete_item(existing_point.id)
            return {
                "status": "success",
                "message": "Item deleted successfully",
                "content_id": update_request.content_id
            }
        else:
            # Update the item
            new_text = update_request.text or existing_point.payload["text"]
            new_metadata = update_request.metadata or existing_point.payload["metadata"]
            
            # Generate new embedding
            new_embedding = embedding_service.generate_embedding(new_text)
            
            # Prepare updated payload
            updated_payload = {
                **existing_point.payload,
                "text": new_text,
                "metadata": new_metadata,
            }
            
            # Update in vector DB
            operation_info = vector_db.update_item(
                point_id=existing_point.id,
                vector=new_embedding,
                payload=updated_payload
            )
            
            return {
                "status": "success",
                "message": "Item updated successfully",
                "content_id": update_request.content_id,
                "details": {
                    "vector_update": bool(new_embedding),
                    "metadata_updated": bool(update_request.metadata),
                    "text_updated": bool(update_request.text)
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing update: {str(e)}"
        )

@router.post("/search/", status_code=status.HTTP_200_OK)
async def search(query: SearchQuery):
    """
    Search the vector database with semantic search
    
    Args:
        query: SearchQuery with text query and optional filters
    
    Returns:
        dict: Search results with scores and metadata
    """
    try:
        # Generate embedding for the query
        query_embedding = embedding_service.generate_embedding(query.query)
        
        # Build search filters
        filters = []
        if query.content_type:
            filters.append({
                "key": "type",
                "match": {"value": query.content_type.value}
            })
        
        if query.filter:
            for key, value in query.filter.items():
                if key.startswith("metadata."):
                    # Handle nested metadata filters
                    metadata_key = key.split(".", 1)[1]
                    filters.append({
                        "key": f"metadata.{metadata_key}",
                        "match": {"value": value}
                    })
                else:
                    filters.append({
                        "key": key,
                        "match": {"value": value}
                    })
        
        # Perform the search
        search_results = vector_db.search(
            vector=query_embedding,
            filter=filters if filters else None,
            limit=query.limit
        )
        
        # Format results
        formatted_results = []
        for result in search_results:
            if result.score > 0.3:
                item = {
                    "content_id": result.payload["content_id"],
                    "type": result.payload["type"],
                    "score": result.score,
                    "text": result.payload["text"][:1000],  # Return first 1000 chars
                    "metadata": result.payload.get("metadata", {}),
                    "created_at": result.payload.get("created_at")
                }
                
                # Add type-specific fields
                if result.payload["type"] == "document":
                    item["filename"] = result.payload.get("filename")
                elif result.payload["type"] == "email":
                    item["subject"] = result.payload.get("subject")
                    item["participants"] = result.payload.get("participants", [])
                
                formatted_results.append(item)
        
        return {
            "status": "success",
            "query": query.query,
            "results": formatted_results,
            "count": len(formatted_results)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )