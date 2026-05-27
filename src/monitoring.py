import asyncio
import subprocess
from time import perf_counter_ns

import psutil

from src.config import HOST_ID, MONITORING_SCOPE

def collect_gpu_resources():
    try:
        out = subprocess.check_output([
            "nvidia-smi",
            "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
            "--format=csv,noheader,nounits"
        ], text=True)

        host_gpu_util_percent, host_vram_used_mb, host_vram_total_mb, host_gpu_temperature = map(
            int,
            out.strip().split(", ")
        )
    except:
        host_gpu_util_percent = None
        host_vram_used_mb = None
        host_vram_total_mb = None
        host_gpu_temperature = None

    return host_gpu_util_percent, host_vram_used_mb, host_vram_total_mb, host_gpu_temperature
     
def collect_resources():
    sample_timestamp_ns = perf_counter_ns()

    host_cpu_percent = psutil.cpu_percent()

    memory = psutil.virtual_memory()
    host_memory_used_mb = memory.used / 1024**2
    host_memory_percent = memory.percent

    disk_io = psutil.disk_io_counters()
    host_disk_read_mb_total = disk_io.read_bytes / 1024**2
    host_disk_write_mb_total = disk_io.write_bytes / 1024**2

    host_gpu_util_percent, host_vram_used_mb, host_vram_total_mb, host_gpu_temperature = collect_gpu_resources()

    resources_sample = {
        "host_id": HOST_ID,
        "monitoring_scope": MONITORING_SCOPE,
        "sample_timestamp_ns": sample_timestamp_ns,
        "host_cpu_percent": host_cpu_percent,
        "host_memory_used_mb": host_memory_used_mb,
        "host_memory_percent": host_memory_percent,
        "host_disk_read_mb_total": host_disk_read_mb_total,
        "host_disk_write_mb_total": host_disk_write_mb_total,
        "host_gpu_util_percent": host_gpu_util_percent,
        "host_vram_used_mb": host_vram_used_mb,
        "host_vram_total_mb": host_vram_total_mb,
        "host_gpu_temperature": host_gpu_temperature,
    }
    return resources_sample

async def monitor_resources(stop_event, resource_samples):
    while not stop_event.is_set():
        resource_samples.append(collect_resources())
        await asyncio.sleep(1)

