import json
from time import perf_counter_ns

from src.config import API_URL


async def run_one_user(client, user_id, llm_model, workload):
    print(f"==> REQUEST: {user_id}")

    result = await chat(client, user_id, llm_model, workload)

    print()
    print(f"<== RESULT: {user_id}")
    print(result)
    print("==========================")
    return result


async def chat(client, user_id, llm_model, workload):

    prompt = workload["prompt"]
    num_predict = workload["num_predict"]

    payload = {
        "model": llm_model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_predict": num_predict
        }
    }

    request_start_ns = perf_counter_ns()

    success = False
    client_ttft_ns = None
    client_total_latency_ns = None
    generation_start_ns = None
    generation_time_ns = None
    output_token_count = 0
    client_tps = None


    async with client.stream("POST", API_URL, json=payload) as response:
        response.raise_for_status()

        async for line in response.aiter_lines():
            if not line:
                continue

            chunk = json.loads(line)

            if chunk.get("error"):
                break

            token = chunk.get("response", "")
            if token:
                if client_ttft_ns is None:
                    now_ns = perf_counter_ns()
                    client_ttft_ns = now_ns - request_start_ns
                    generation_start_ns = now_ns
                #print(token, end="", flush=True)
                # for debugging, !can be mixed with concurrency

            if chunk.get("done") is True:
                done_ns = perf_counter_ns()
                client_total_latency_ns = done_ns - request_start_ns
                output_token_count = chunk.get("eval_count", 0)

                if generation_start_ns is not None:
                    generation_time_ns = done_ns - generation_start_ns

                    if output_token_count:
                        client_tps = output_token_count / (generation_time_ns / 1_000_000_000)
                success = True
                break

    request_metrics = {
        "user_id": user_id,
        "llm_model": llm_model,
        "success": success,
        "client_ttft_ns": client_ttft_ns,
        "client_total_latency_ns": client_total_latency_ns,
        "client_tps": client_tps,
        "workload_name": workload["name"],
        "num_predict": workload["num_predict"],
        "prompt_category": workload["prompt_category"],
        "output_category": workload["output_category"],
    }
    return request_metrics

