from typing import Dict
import uuid
from datetime import datetime

def generate_content_id() -> str:
    return str(uuid.uuid4())

def generate_point_id() -> str:
    return str(uuid.uuid4())

def get_current_datetime() -> str:
    return datetime.now().isoformat()

def create_payload(item, content_id: str) -> Dict:
    payload = {
        "content_id": content_id,
        "text": item.text,
        "type": item.type.value,
        "metadata": item.metadata,
        "created_at": get_current_datetime()
    }
    
    if item.type == "document" and item.filename:
        payload["filename"] = item.filename
    elif item.type == "email" and item.subject:
        payload["subject"] = item.subject
    if item.type in ["email", "call_transcript"] and item.participants:
        payload["participants"] = item.participants
    
    return payload