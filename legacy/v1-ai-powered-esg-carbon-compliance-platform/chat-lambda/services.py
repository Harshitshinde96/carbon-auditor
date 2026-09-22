import time
import uuid
import datetime
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from google import genai
from utils import logger, get_env_var

# Initialize clients globally
dynamodb = boto3.resource('dynamodb')

# Initialize GenAI Client globally
_genai_client = None

def get_genai_client():
    global _genai_client
    if not _genai_client:
        api_key = get_env_var('GEMINI_API_KEY')
        _genai_client = genai.Client(api_key=api_key)
    return _genai_client

def retrieve_user_bills(user_id: str) -> list:
    """Retrieves bills from DynamoDB. Designed to be replaced by Qdrant retrieval later."""
    start_time = time.time()
    logger.info(f"START - Retrieving bills for userId: {user_id}")
    
    table_name = get_env_var('BILL_METADATA_TABLE')
    table = dynamodb.Table(table_name)
    bills = []
    
    try:
        response = table.query(
            IndexName='userId-index',
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        bills.extend(response.get('Items', []))
        while 'LastEvaluatedKey' in response:
            response = table.query(
                IndexName='userId-index',
                KeyConditionExpression=Key('userId').eq(user_id),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            bills.extend(response.get('Items', []))
    except ClientError as e:
        logger.warning(f"GSI query failed, falling back to scan: {e}")
        response = table.scan(FilterExpression=Attr('userId').eq(user_id))
        bills.extend(response.get('Items', []))
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Attr('userId').eq(user_id),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            bills.extend(response.get('Items', []))
            
    completed_bills = [b for b in bills if b.get('processingStatus') == 'COMPLETED']
    # Sort by billingMonth
    sorted_bills = sorted(completed_bills, key=lambda x: x.get('billingMonth', ''))
    
    duration = round(time.time() - start_time, 2)
    logger.info(f"SUCCESS - Retrieved {len(sorted_bills)} bills for userId: {user_id}. Processing time: {duration}s")
    return sorted_bills

def create_structured_context(bills: list) -> str:
    """Formats retrieved bills into a prompt context."""
    if not bills:
        return "No completed bills on record."
        
    context = "USER BILLING HISTORY:\n"
    for b in bills:
        month = b.get('billingMonth', 'Unknown Month')
        b_type = b.get('billType', 'Unknown Type')
        amount = b.get('billAmount', 0)
        curr = b.get('currency', 'INR')
        units = b.get('unitsConsumed', 0)
        carbon = b.get('carbonEmission', 0)
        context += f"- {month} ({b_type}): Amount: {amount} {curr}, Consumed: {units}, Carbon Emission: {carbon} kgCO2e\n"
    return context

def generate_ai_response(context: str, message: str) -> str:
    """Calls Gemini via google-genai SDK."""
    start_time = time.time()
    logger.info("START - Calling Gemini API")
    
    client = get_genai_client()
    model_name = get_env_var('GEMINI_MODEL')
    
    prompt = (
        "You are the Carbon Auditor AI Assistant.\n"
        "Use the following user bill history to answer their question concisely and accurately.\n"
        f"{context}\n\n"
        f"User Question: {message}"
    )
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        duration = round(time.time() - start_time, 2)
        logger.info(f"SUCCESS - Gemini API returned response. Processing time: {duration}s")
        return response.text
    except Exception as e:
        duration = round(time.time() - start_time, 2)
        logger.error(f"FAILED - Gemini API Error. Processing time: {duration}s. Error: {e}")
        raise ValueError("Failed to generate response from AI.")

def store_conversation(user_id: str, message: str, answer: str, processing_time: float) -> str:
    """Stores the chat history in DynamoDB."""
    start_time = time.time()
    chat_id = str(uuid.uuid4())
    logger.info(f"START - Storing conversation for chatId: {chat_id}")
    
    table_name = get_env_var('CHAT_TABLE')
    table = dynamodb.Table(table_name)
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    
    item = {
        'chatId': chat_id,
        'userId': user_id,
        'message': message,
        'response': answer,
        'timestamp': timestamp,
        'processingTime': str(round(processing_time, 2))
    }
    
    try:
        table.put_item(Item=item)
        duration = round(time.time() - start_time, 2)
        logger.info(f"SUCCESS - Stored conversation chatId: {chat_id}. Processing time: {duration}s")
    except ClientError as e:
        duration = round(time.time() - start_time, 2)
        logger.error(f"FAILED - DynamoDB store failure for chatId: {chat_id}. Processing time: {duration}s. Error: {e}")
        
    return chat_id
