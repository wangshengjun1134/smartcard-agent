"""Test LLM API latency - compare stream vs non-stream (OpenAI SDK)."""

import asyncio
import time
import sys
import os

sys.path.insert(0, 'src')

# Force output
os.environ['PYTHONUNBUFFERED'] = '1'

# 应用的意图分类 prompt
INTENT_PROMPT_TEXT = """你是一个智能卡操作意图分析器。

分析用户请求，确定执行意图类型。

可选意图类型：
- NORMAL_CHAT: 普通问答，如问候、帮助请求，直接回复即可
- RAG_DOMINANT: RAG主导，主要是知识查询，如"什么是IMSI"、"解释SCP03"
- TOOL_REASONING: 工具/推理主导，需要执行卡片操作，如"读取IMSI"、"建立安全通道"

用户请求: {input}

请返回意图类型，仅返回类型名称，不要解释。

意图类型:"""


async def test_openai_stream():
    """Test using OpenAI SDK streaming."""
    from openai import AsyncOpenAI
    from llm.config import LLMConfig

    cfg = LLMConfig.get_config()
    client = AsyncOpenAI(
        api_key=cfg.openai_api_key,
        base_url=cfg.openai_api_base
    )

    user_input = '333'
    t0 = time.time()
    first_chunk = None
    chunks = []

    stream = await client.chat.completions.create(
        model=cfg.openai_model,
        messages=[{'role': 'user', 'content': INTENT_PROMPT_TEXT.format(input=user_input)}],
        stream=True
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            chunks.append(content)
            if first_chunk is None:
                first_chunk = time.time() - t0

    total_time = time.time() - t0
    full_response = ''.join(chunks)
    stream_speed = len(full_response) / (total_time - first_chunk) if total_time > first_chunk else 0

    return {
        'method': 'OpenAI stream',
        'first_chunk': first_chunk,
        'total_time': total_time,
        'response_len': len(full_response),
        'chunk_count': len(chunks),
        'stream_speed': stream_speed,
        'response': full_response
    }


async def test_openai_non_stream():
    """Test using OpenAI SDK non-streaming (invoke)."""
    from openai import AsyncOpenAI
    from llm.config import LLMConfig

    cfg = LLMConfig.get_config()
    client = AsyncOpenAI(
        api_key=cfg.openai_api_key,
        base_url=cfg.openai_api_base
    )

    user_input = '333'
    t0 = time.time()

    response = await client.chat.completions.create(
        model=cfg.openai_model,
        messages=[{'role': 'user', 'content': INTENT_PROMPT_TEXT.format(input=user_input)}],
        stream=False
    )

    total_time = time.time() - t0
    content = response.choices[0].message.content

    return {
        'method': 'OpenAI non-stream',
        'first_chunk': total_time,  # Non-stream: first chunk = total time
        'total_time': total_time,
        'response_len': len(content),
        'chunk_count': 1,
        'stream_speed': len(content) / 0.001 if total_time > 0 else 0,  # Instant delivery
        'response': content
    }


async def test_langchain_stream():
    """Test using LangChain astream."""
    from llm.config import LLMConfig
    from llm.llm import get_llm
    from langchain_core.prompts import ChatPromptTemplate

    cfg = LLMConfig.get_config()
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(INTENT_PROMPT_TEXT)
    chain = prompt | llm

    user_input = '333'
    t0 = time.time()
    first_chunk = None
    chunks = []

    async for chunk in chain.astream({'input': user_input}):
        chunk_str = str(chunk.content) if hasattr(chunk, 'content') else str(chunk)
        chunks.append(chunk_str)
        if first_chunk is None:
            first_chunk = time.time() - t0

    total_time = time.time() - t0
    full_response = ''.join(chunks)
    stream_speed = len(full_response) / (total_time - first_chunk) if total_time > first_chunk else 0

    return {
        'method': 'LangChain astream',
        'first_chunk': first_chunk,
        'total_time': total_time,
        'response_len': len(full_response),
        'chunk_count': len(chunks),
        'stream_speed': stream_speed,
        'response': full_response
    }


async def test_langchain_non_stream():
    """Test using LangChain invoke (non-streaming)."""
    from llm.config import LLMConfig
    from llm.llm import get_llm
    from langchain_core.prompts import ChatPromptTemplate

    cfg = LLMConfig.get_config()
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(INTENT_PROMPT_TEXT)
    chain = prompt | llm

    user_input = '333'
    t0 = time.time()

    result = await chain.ainvoke({'input': user_input})

    total_time = time.time() - t0
    content = result.content

    return {
        'method': 'LangChain invoke',
        'first_chunk': total_time,
        'total_time': total_time,
        'response_len': len(content),
        'chunk_count': 1,
        'stream_speed': len(content) / 0.001,
        'response': content
    }


async def test_llm():
    from llm.config import LLMConfig

    cfg = LLMConfig.get_config()
    print(f'Model: {cfg.openai_model}', flush=True)
    print(f'Base URL: {cfg.openai_api_base}', flush=True)

    print('\n' + '='*60, flush=True)
    print('COMPARISON: Stream vs Non-Stream (both SDKs)', flush=True)
    print('='*60, flush=True)

    methods = [
        ('LangChain astream', test_langchain_stream),
        ('LangChain invoke', test_langchain_non_stream),
        ('OpenAI stream', test_openai_stream),
        ('OpenAI non-stream', test_openai_non_stream),
    ]

    results = {}

    for name, test_func in methods:
        print(f'\n--- {name} ---', flush=True)
        method_results = []
        for i in range(5):
            result = await test_func()
            method_results.append(result)
            print(f'  Run {i+1}: First={result["first_chunk"]:.2f}s, Total={result["total_time"]:.2f}s', flush=True)
            print(f'          Len={result["response_len"]}, Chunks={result["chunk_count"]}, Speed={result["stream_speed"]:.1f} chars/sec', flush=True)
        results[name] = method_results

    # Summary
    print('\n' + '='*60, flush=True)
    print('SUMMARY', flush=True)
    print('='*60, flush=True)

    for name, method_results in results.items():
        avg_total = sum(r['total_time'] for r in method_results) / len(method_results)
        avg_first = sum(r['first_chunk'] for r in method_results) / len(method_results)
        avg_chunks = sum(r['chunk_count'] for r in method_results) / len(method_results)
        avg_speed = sum(r['stream_speed'] for r in method_results) / len(method_results)
        print(f'{name}:', flush=True)
        print(f'  First chunk: {avg_first:.2f}s, Total: {avg_total:.2f}s, Chunks: {avg_chunks:.0f}', flush=True)
        print(f'  Stream speed: {avg_speed:.1f} chars/sec', flush=True)

    print('\n' + '='*60, flush=True)
    print('KEY INSIGHT', flush=True)
    print('='*60, flush=True)
    print('If non-stream is faster than stream, the API server is slow.', flush=True)
    print('If LangChain is slower than OpenAI SDK, LangChain adds overhead.', flush=True)


if __name__ == '__main__':
    asyncio.run(test_llm())