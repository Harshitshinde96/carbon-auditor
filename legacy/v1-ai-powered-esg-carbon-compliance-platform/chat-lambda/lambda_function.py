import json
import time
from utils import logger, build_response, validate_chat_request
from services import (
    retrieve_user_bills,
    create_structured_context,
    generate_ai_response,
    store_conversation
)

def lambda_handler(event, context):
    logger.info(f"START - Processing Chat Request: {json.dumps(event.get('body', '{}'))}")
    overall_start = time.time()
    
    try:
        # Parse body
        body_str = event.get('body', '{}')
        body = json.loads(body_str) if isinstance(body_str, str) else body_str
        
        # Validate
        user_id, message = validate_chat_request(body)
        
        # Process
        bills = retrieve_user_bills(user_id)
        chat_context = create_structured_context(bills)
        
        ai_response = generate_ai_response(chat_context, message)
        
        # Calculate time before saving
        processing_time = time.time() - overall_start
        chat_id = store_conversation(user_id, message, ai_response, processing_time)
        
        logger.info(f"SUCCESS - Chat request completed for userId: {user_id}, chatId: {chat_id}. Total time: {round(processing_time, 2)}s")
        
        return build_response(200, {
            "success": True,
            "answer": ai_response,
            "chatId": chat_id
        })
        
    except ValueError as ve:
        logger.error(f"FAILED - Validation/Business Logic Error: {str(ve)}")
        return build_response(400, {"success": False, "message": str(ve)})
    except Exception as e:
        logger.error(f"FAILED - Unexpected Internal Error: {str(e)}", exc_info=True)
        return build_response(500, {"success": False, "message": "Internal Server Error"})
