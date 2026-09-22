import asyncio, time
from app.services.rag_service import RAGService
print('Init...')
t0=time.time()
s = RAGService()
print(f'Init done in {time.time()-t0:.2f}s')
async def test():
    t1=time.time()
    v = await s._embed_query('hi')
    print(f'Embed done in {time.time()-t1:.2f}s')
    t2=time.time()
    p = await s._search_qdrant(v)
    print(f'Search done in {time.time()-t2:.2f}s')
    t3=time.time()
    try:
        await s._generate_gemini_response('say hi')
    except Exception as e:
        print('Gemini error:', e)
    print(f'Gemini done in {time.time()-t3:.2f}s')
asyncio.run(test())
