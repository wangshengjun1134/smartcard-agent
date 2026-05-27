"""Test timing for various components."""

import sys
import asyncio
import time

sys.path.insert(0, 'src')


async def main():
    print("=== Timing Analysis ===\n")

    # 1. Intent node
    print("1. Testing Intent node...")
    from agents.graph.state import create_initial_state
    from agents.nodes.intent.intent_node import intent_node
    state = create_initial_state("你好")
    t0 = time.time()
    result = intent_node(state)
    print(f"   Intent: {time.time() - t0:.3f}s, result={result.get('execution_intent')}")

    # 2. LLM config (first time - no cache)
    print("\n2. Testing LLM config (first time, no cache)...")
    t0 = time.time()
    from llm.config import LLMConfig
    cfg = LLMConfig.get_config()
    first_config_time = time.time() - t0
    print(f"   Config (1st): {first_config_time:.3f}s")
    print(f"   model={cfg.openai_model}, base_url={cfg.openai_api_base}")

    # 2b. LLM config (second time - cached)
    print("\n2b. Testing LLM config (second time, cached)...")
    t0 = time.time()
    cfg2 = LLMConfig.get_config()
    cached_config_time = time.time() - t0
    print(f"   Config (2nd): {cached_config_time:.3f}s")

    # 3. LLM init
    print("\n3. Testing LLM init...")
    t0 = time.time()
    from llm.llm import get_llm
    llm = get_llm()
    print(f"   LLM init: {time.time() - t0:.3f}s")

    # 4. LLM stream
    print("\n4. Testing LLM stream...")
    from langchain_core.prompts import ChatPromptTemplate
    prompt = ChatPromptTemplate.from_template("简短回复: {input}")
    chain = prompt | llm
    t0 = time.time()
    first_chunk_time = None
    chunks = 0
    async for chunk in chain.astream({"input": "你好"}):
        if first_chunk_time is None:
            first_chunk_time = time.time()
        chunks += 1
    total_time = time.time() - t0
    first_chunk_delay = first_chunk_time - t0 if first_chunk_time else total_time
    print(f"   First chunk: {first_chunk_delay:.3f}s")
    print(f"   Total stream: {total_time:.3f}s")
    print(f"   Total chunks: {chunks}")

    print("\n=== Summary ===")
    print(f"First request total: ~{first_config_time + 1.0 + first_chunk_delay:.3f}s")
    print(f"Cached request total: ~{cached_config_time + 1.0 + first_chunk_delay:.3f}s")


if __name__ == "__main__":
    asyncio.run(main())