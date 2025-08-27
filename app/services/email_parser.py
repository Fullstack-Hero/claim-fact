import asyncio
import json
from typing import Dict, Any
from openai import OpenAI
from fastapi import HTTPException
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmailParserService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
    
    async def parse_email_thread(self, email_content: str) -> Dict[str, Any]:
        """
        Parse an email thread using OpenAI API and return structured JSON
        Uses GPT-4 Turbo with 128K context window for handling long email threads
        
        Args:
            email_content: The email thread content to parse
            
        Returns:
            Dict containing the parsed email thread structure
        """
        try:
            
            if not email_content:
                raise HTTPException(status_code=400, detail="No email content provided")
            prompt = f"""
            Analyze this email thread and extract ALL individual emails into a structured JSON format.
            The output should follow this exact structure:

            {{
                "success": true,
                "message": "Email thread parsed successfully",
                "data": {{
                    "threadInfo": {{
                        "totalEmails": <number>
                    }},
                    "emails": [
                        {{
                            "index": 1,
                            "from": {{
                                "email": "string",
                                "name": "string",
                                "type": "email"
                            }},
                            "to": [
                                {{
                                    "email": "string",
                                    "name": "string",
                                    "type": "email"
                                }}
                            ],
                            "cc": [
                                {{
                                    "email": "string",
                                    "name": "string",
                                    "type": "email"
                                }}
                            ],
                            "subject": "string",
                            "date": "ISO8601 date string",
                            "contentPreview": "COMPLETE content of email",
                            "isMainEmail": boolean
                        }}
                    ]
                }}
            }}

            Instructions:
            1. Identify ALL individual emails in the thread - do not skip any emails
            2. Parse "From", "To", "CC" fields into structured objects
            3. Extract email addresses and names separately
            4. Determine the threading level based on indentation/quoting
            5. The first email should have "isMainEmail": true
            6. Convert all dates to ISO 8601 format
            8. Count the total number of emails accurately
            9. CRITICAL: Ensure the JSON response is complete and not truncated

            Email thread content:
            {email_content}
            """
            # Call OpenAI API with GPT-4o (better token limits)
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4o",  # Use GPT-4o which has better token limits
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert email parser. Extract ALL emails from email threads with COMPLETE content. Do not summarize, truncate, or omit any part of the email content. Include signatures, disclaimers, and all footer text. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent parsing
                max_tokens=16000  # Standard token limit for GPT-4o
            )
            # Extract the JSON response
            result_text = response.choices[0].message.content.strip()
            
            # Check if response was truncated
            if response.choices[0].finish_reason == "length":
                raise HTTPException(
                    status_code=500, 
                    detail="Response was truncated due to token limit. The email thread is too long to parse completely."
                )
            # Clean the response (remove markdown code blocks if present)
            if result_text.startswith("```json"):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith("```"):
                result_text = result_text[3:-3].strip()
            
            # Parse the JSON response
            try:
                parsed_result = json.loads(result_text)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to parse JSON response from OpenAI: {str(e)}. Response may have been truncated."
                )
            
            return parsed_result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error parsing email thread: {str(e)}") 