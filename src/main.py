import asyncio
import httpx
import json
import psutil
import subprocess
from time import perf_counter_ns

URL= "http://localhost:11434/api/generate"
HOST_ID = "localhost"
MONITORING_SCOPE = "ollama_host_local"
LLM_MODEL = "llama3.1:8b"

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


def collect_gpu_resources():
    try:
        out = subprocess.check_output([
            "nvidia-smi",
            "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
            "--format=csv,noheader,nounits"
        ], text=True)

        host_gpu_util_percent, host_vram_used, host_vram_total_mb, host_gpu_temperature = map(
            int,
            out.strip().split(", ")
        )
    except:
        host_gpu_util_percent = None
        host_vram_used = None
        host_vram_total_mb = None
        host_gpu_temperature = None

    return host_gpu_util_percent, host_vram_used, host_vram_total_mb, host_gpu_temperature
     

def collect_resources():
    sample_timestamp_ns = perf_counter_ns()

    host_cpu_percent = psutil.cpu_percent()

    memory = psutil.virtual_memory()
    host_memory_used = memory.used / 1024**2
    host_memory_percent = memory.percent

    disk_io = psutil.disk_io_counters()
    host_disk_read_mb_total = disk_io.read_bytes / 1024**2
    host_disk_write_mb_total = disk_io.write_bytes / 1024**2

    host_gpu_util_percent, host_vram_used, host_vram_total_mb, host_gpu_temperature = collect_gpu_resources()

    resources_sample = {
        "host_id": HOST_ID,
        "monitoring_scope": MONITORING_SCOPE,
        "sample_timestamp_ns": sample_timestamp_ns,
        "host_cpu_percent": host_cpu_percent,
        "host_memory_used": host_memory_used,
        "host_memory_percent": host_memory_percent,
        "host_disk_read_mb_total": host_disk_read_mb_total,
        "host_disk_write_mb_total": host_disk_write_mb_total,
        "host_gpu_util_percent": host_gpu_util_percent,
        "host_vram_used": host_vram_used,
        "host_vram_total_mb": host_vram_total_mb,
        "host_gpu_temperature": host_gpu_temperature,
    }
    return resources_sample

async def monitor_resources(stop_event, resource_samples):
    while not stop_event.is_set():
        resource_samples.append(collect_resources())
        await asyncio.sleep(1)

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

    return {
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

async def main():
    llm_model = LLM_MODEL
    user_amount = 3
    results = []
    resource_samples = []
    workload = WORKLOADS["short_prompt_short_output"]
    benchmark_start_ns = perf_counter_ns()
    stop_event = asyncio.Event()

    async with httpx.AsyncClient(timeout=None) as client:
        monitor_task = asyncio.create_task(
            monitor_resources(stop_event, resource_samples)
        )

        tasks = [
            run_one_user(client, i+1, llm_model, workload)
            for i in range(user_amount)
        ]
        results = await asyncio.gather(*tasks)

        stop_event.set()
        await monitor_task

    request_count = len(results)
    success_count = sum(1 for result in results if result["success"])
    success_rate = success_count / request_count

    total_time_s = (perf_counter_ns() - benchmark_start_ns) / 1_000_000_000
    rps = request_count / total_time_s

    print()
    print(f"=== SIMULATION IS DONE ===")
    print(f"SUCCESS RATE: {success_rate * 100:.0f}%")
    print(f"RPS: {rps:.2f}")
    print(f"DURATION: {total_time_s:.2f}s")

    print(f"RESOURCE SAMPLES: {len(resource_samples)}")
    print(f"FIRST SAMPLE: {resource_samples[0]}")
    print(f"LAST SAMPLE: {resource_samples[-1]}")

if __name__ == "__main__":
    asyncio.run(main())

