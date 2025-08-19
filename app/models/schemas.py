from enum import Enum
from typing import List, Dict, Union, Optional
from pydantic import BaseModel

class ContentType(str, Enum):
    DOCUMENT = "document"
    EMAIL = "email"
    CALL_TRANSCRIPT = "call_transcript"

class ContentItem(BaseModel):
    text: str
    type: ContentType
    metadata: Dict[str, Union[str, int, float, bool]] = {}
    filename: Optional[str] = None
    subject: Optional[str] = None
    participants: Optional[List[str]] = None

class AddResponse(BaseModel):
    id: str
    content_id: str
    type: ContentType
    metadata: Dict[str, Union[str, int, float, bool]]

class UpdateRequest(BaseModel):
    content_id: str
    text: Optional[str] = None
    metadata: Optional[Dict[str, Union[str, int, float, bool]]] = None
    remove: bool = False

class SearchQuery(BaseModel):
    query: str
    filter: Optional[Dict] = None
    limit: int = 5
    content_type: Optional[ContentType] = None