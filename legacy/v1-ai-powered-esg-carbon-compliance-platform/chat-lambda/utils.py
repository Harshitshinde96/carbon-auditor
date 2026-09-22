import os
import json
import logging
from typing import Dict, Any

# Professional Logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

def get_env_var(var_name: str) -> str:
    """Safely retrieves an environment variable."""
    value = os.environ.get(var_name)
    if not value:
        raise ValueError(f"Missing required environment variable: {var_name}")
    return value

def build_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures consistent CORS and JSON formatting for API Gateway."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        },
        "body": json.dumps(body)
    }

def validate_chat_request(body: Dict[str, Any]) -> tuple[str, str]:
    """Validates the incoming API payload."""
    user_id = body.get('userId')
    message = body.get('message')
    
    if not user_id:
        raise ValueError("Missing required parameter: userId")
    if not message or not str(message).strip():
        raise ValueError("Missing required parameter: message")
        
    return str(user_id), str(message)
