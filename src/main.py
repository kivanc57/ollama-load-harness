import os
import asyncio
import httpx
from pathlib import Path
from time import perf_counter_ns

from src.config import LLM_MODEL, USER_AMOUNT
from src.workloads import WORKLOADS
from src.client import run_one_user
from src.monitoring import monitor_resources
from src.results import write_results

async def main():
    user_amount = USER_AMOUNT
    llm_model = LLM_MODEL
    workload = WORKLOADS["short_prompt_short_output"]

    request_metrics = []
    resource_samples = []
    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir.parent / "output"
    os.makedirs(output_dir, exist_ok=True) # exist dir if not present
    request_metrics_path = output_dir / "client_metrics.csv"
    resource_samples_path = output_dir / "host_metrics.csv"

    stop_event = asyncio.Event()
    benchmark_start_ns = perf_counter_ns()

    async with httpx.AsyncClient(timeout=None) as client:
        monitor_task = asyncio.create_task(
            monitor_resources(stop_event, resource_samples)
        )

        tasks = [
            run_one_user(client, i+1, llm_model, workload)
            for i in range(user_amount)
        ]
        request_metrics = await asyncio.gather(*tasks)

        stop_event.set()
        await monitor_task

    request_count = len(request_metrics)
    success_count = sum(1 for result in request_metrics if result["success"])
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

    write_results(resource_samples, resource_samples_path)
    write_results(request_metrics, request_metrics_path)

    print(f"\n==> RESULTS ARE WRITTEN IN: {output_dir}")

if __name__ == "__main__":
    asyncio.run(main())

