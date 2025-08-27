from enum import Enum
from typing import List, Dict, Union, Optional, Any
from pydantic import BaseModel, Field

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


class EmailData(BaseModel):
    # Your provided email data structure
    Content_Type: Optional[str] = Field(None, alias="Content-Type")
    Date: Optional[str] = None
    Dkim_Signature: Optional[str] = Field(None, alias="Dkim-Signature")
    From: Optional[str] = None
    In_Reply_To: Optional[str] = Field(None, alias="In-Reply-To")
    Message_Id: Optional[str] = Field(None, alias="Message-Id")
    Mime_Version: Optional[str] = Field(None, alias="Mime-Version")
    Received: Optional[str] = None
    References: Optional[str] = None
    Subject: Optional[str] = None
    To: Optional[str] = None
    X_Envelope_From: Optional[str] = Field(None, alias="X-Envelope-From")
    X_Gm_Features: Optional[str] = Field(None, alias="X-Gm-Features")
    X_Gm_Gg: Optional[str] = Field(None, alias="X-Gm-Gg")
    X_Gm_Message_State: Optional[str] = Field(None, alias="X-Gm-Message-State")
    X_Google_Dkim_Signature: Optional[str] = Field(None, alias="X-Google-Dkim-Signature")
    X_Google_Smtp_Source: Optional[str] = Field(None, alias="X-Google-Smtp-Source")
    X_Mailgun_Incoming: Optional[str] = Field(None, alias="X-Mailgun-Incoming")
    X_Received: Optional[str] = Field(None, alias="X-Received")
    
    # Email body content (using actual JSON field names with hyphens)
    body_html: Optional[str] = Field(None, alias="body-html")
    body_plain: Optional[str] = Field(None, alias="body-plain")
    stripped_html: Optional[str] = Field(None, alias="stripped-html")
    stripped_text: Optional[str] = Field(None, alias="stripped-text")
    stripped_signature: Optional[str] = Field(None, alias="stripped-signature")
    
    # Additional fields
    from_: Optional[str] = Field(None, alias="from")
    subject: Optional[str] = None
    
    # Mailgun specific fields
    recipient: Optional[str] = None
    sender: Optional[str] = None
    signature: Optional[str] = None
    timestamp: Optional[str] = None
    token: Optional[str] = None
    message_headers: Optional[str] = Field(None, alias="message-headers")
    
    class Config:
        populate_by_name = True


class EmailThreadRequest(BaseModel):
    email_data: EmailData