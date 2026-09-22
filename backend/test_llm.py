import asyncio, logging
logging.basicConfig(level=logging.INFO)
from app.core.llm_client import OpenRouterClient
async def test():
    c = OpenRouterClient()
    response = await c.client.chat.completions.create(model='nvidia/nemotron-3-ultra-550b-a55b:free', messages=[{'role': 'user', 'content': 'Hi'}])
    print('Result:', response)
asyncio.run(test())
