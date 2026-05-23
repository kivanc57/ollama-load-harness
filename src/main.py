import asyncio
import httpx
import json
from time import perf_counter_ns

URL= "http://localhost:11434/api/generate"

MODEL = "llama3.1:8b"
MODEL2 = "gemma3:4b"
PROMPT = 'what is 2 x 2 = ?'

async def run_one_user(client, user_id):
    print(f"==> REQUEST: {user_id}")
    
    result = await chat(client, MODEL, PROMPT)

    print(f"\nRESULT: {user_id}")
    print(result)
    print("==========================")
    return result

async def chat(client, model, prompt):

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
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
    }

async def main():
    user_amount = 3
    results = []

    benchmark_start_ns = perf_counter_ns()

    async with httpx.AsyncClient(timeout=None) as client:
        tasks = [
            run_one_user(client, i+1)
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

