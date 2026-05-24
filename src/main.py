import asyncio
import httpx
import json
from time import perf_counter_ns

URL= "http://localhost:11434/api/generate"

#MODEL = "llama3.1:8b"
#MODEL2 = "gemma3:4b"

LONG_CONTEXT = """
Linguistic relativity asserts that language influences worldview or cognition. One form of linguistic relativity, linguistic determinism, regards peoples' languages as determining and influencing the scope of cultural perceptions of their surrounding world.

Various colloquialisms refer to linguistic relativism: the Whorf hypothesis; the Sapir–Whorf hypothesis (/səˌpɪər ˈhwɔːrf/ sə-PEER WHORF); the Whorf–Sapir hypothesis; and Whorfianism.

The hypothesis is disputed, with many different variations throughout its history.The strong hypothesis of linguistic relativity, now referred to as linguistic determinism, is that language determines thought and that linguistic categories limit and restrict cognitive categories. This was a claim by some earlier linguists pre-World War II; since then it has fallen out of acceptance by contemporary linguists. Nevertheless, research has produced positive empirical evidence supporting a weaker version of linguistic relativity: that a language's structures influence a speaker's perceptions, without strictly limiting or obstructing them.

Although common, the term Sapir–Whorf hypothesis is sometimes considered a misnomer for several reasons. Edward Sapir (1884–1939) and Benjamin Lee Whorf (1897–1941) never stated their ideas in terms of a hypothesis. The distinction between a weak and a strong version of this hypothesis is also a later development; Sapir and Whorf never used such a dichotomy, although often their writings and their opinions of this relativity principle expressed it in stronger or weaker terms.

The principle of linguistic relativity and the relationship between language and thought has also received attention in varying academic fields, including philosophy, psychology and anthropology. It has also influenced works of fiction and the invention of constructed languages.

Source: Wikipedia excerpt on linguistic relativity.
"""

WORKLOADS = {
    "short_prompt_short_output":
    {
        "name": "short_prompt_short_output",
        "num_predict": 32,
        "prompt": "What is 2 + 2? Answer in one sentence.",
        "prompt_category": "short",
        "output_category": "short",
    },

    "short_prompt_long_output":
    {
        "name": "short_prompt_long_output",
        "num_predict": 256,
        "prompt": "Explain the difference between CPU and GPU processing in simple terms.",
        "prompt_category": "short",
        "output_category": "long",
    },

    "long_prompt_short_output":
    {
        "name": "long_prompt_short_output",
        "num_predict": 32,
        "prompt": LONG_CONTEXT + "\n\nBased on the text above, answer in one sentence: what is the main topic?",
        "prompt_category": "long",
        "output_category": "short",
    },

    "long_prompt_long_output":
    {
        "name": "long_prompt_long_output",
        "num_predict": 256,
        "prompt": LONG_CONTEXT + "\n\nSummarize the text above and explain its main implications.",
        "prompt_category": "long",
        "output_category": "long",
    },
}

async def run_one_user(client, user_id, model, workload):
    print(f"==> REQUEST: {user_id}")

    result = await chat(client, model, workload)

    print(f"\nRESULT: {user_id}")
    print(result)
    print("==========================")
    return result

async def chat(client, model, workload):

    prompt = workload["prompt"]
    num_predict = workload["num_predict"]

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_predict": num_predict
        }
    }

    request_start_ns = perf_counter_ns()

    success = False
    ttft_ns = None
    total_latency_ns = None
    generation_start_ns = None
    generation_time_ns = None
    output_token_count = 0
    tps = None


    async with client.stream("POST", URL, json=payload) as response:
        response.raise_for_status()

        async for line in response.aiter_lines():
            if not line:
                continue

            chunk = json.loads(line)

            if chunk.get("error"):
                break

            token = chunk.get("response", "")
            if token:
                if ttft_ns is None:
                    now_ns = perf_counter_ns()
                    ttft_ns = now_ns - request_start_ns
                    generation_start_ns = now_ns
                #print(token, end="", flush=True)
                # for debugging, !can be mixed with concurrency

            if chunk.get("done") is True:
                done_ns = perf_counter_ns()
                total_latency_ns = done_ns - request_start_ns
                output_token_count = chunk.get("eval_count", 0)

                if generation_start_ns is not None:
                    generation_time_ns = done_ns - generation_start_ns

                    if output_token_count:
                        tps = output_token_count / (generation_time_ns / 1_000_000_000)
                success = True
                break

    return {
        "model": model,
        "success": success,
        "ttft_ns": ttft_ns,
        "total_latency_ns": total_latency_ns,
        "tps": tps,
        "workload_name": workload["name"],
        "num_predict": workload["num_predict"],
        "prompt_category": workload["prompt_category"],
        "output_category": workload["output_category"],
    }

async def main():
    model = "llama3.1:8b"
    user_amount = 3
    results = []
    workload = WORKLOADS["long_prompt_long_output"]

    benchmark_start_ns = perf_counter_ns()

    async with httpx.AsyncClient(timeout=None) as client:
        tasks = [
            run_one_user(client, i+1, model, workload)
            for i in range(user_amount)
        ]
        results = await asyncio.gather(*tasks)

    request_count = len(results)
    success_count = sum(1 for result in results if result["success"])
    success_rate = success_count / request_count

    total_time_s = (perf_counter_ns() - benchmark_start_ns) / 1_000_000_000
    rps = request_count / total_time_s

    print()
    print(f"=== SIMULATION IS DONE ===")
    print(f"=== SUCCESS RATE: {success_rate * 100:.0f}%")
    print(f"=== RPS: {rps:.2f}")
    print(f"=== DURATION: {total_time_s:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())

