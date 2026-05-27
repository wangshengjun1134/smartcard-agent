"""Test LLM API latency."""

import asyncio
import time
import sys
import os

sys.path.insert(0, 'src')

# Force output
os.environ['PYTHONUNBUFFERED'] = '1'


async def test_llm():
    from llm.config import LLMConfig
    from llm.llm import get_llm
    from langchain_core.prompts import ChatPromptTemplate

    # Use cached config
    cfg = LLMConfig.get_config()
    print(f'Model: {cfg.openai_model}', flush=True)
    print(f'Base URL: {cfg.openai_api_base}', flush=True)

    llm = get_llm()
    prompt = ChatPromptTemplate.from_template('回复: {input}')
    chain = prompt | llm

    print('\nTesting LLM API latency...', flush=True)

    # Test 3 times
    results = []
    for i in range(3):
        t0 = time.time()
        first_chunk = None
        async for chunk in chain.astream({'input': '你好'}):
            if first_chunk is None:
                first_chunk = time.time() - t0
                results.append(first_chunk)
                print(f'  Run {i+1}: First chunk = {first_chunk:.2f}s', flush=True)
                break

    avg = sum(results) / len(results)
    print(f'\nAverage first chunk latency: {avg:.2f}s', flush=True)


if __name__ == '__main__':
    asyncio.run(test_llm())