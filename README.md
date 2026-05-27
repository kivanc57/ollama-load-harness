# Ollama Load Testing Harness

This project is a Proof of Concept load-testing harness for Ollama. It simulates concurrent users sending streaming inference requests, records client-side latency and throughput metrics, and samples host-level resource metrics during the benchmark.

The goal is not to build a production-grade benchmark platform, but to demonstrate how concurrency, workload shape, request metrics, and host metrics can be correlated to reason about bottlenecks. The harness does not automatically prove a single root cause. Instead, it provides correlated signals that can be used to infer likely bottlenecks.

**The observer effect** is reduced by keeping the harness lightweight: streamed tokens are not printed during benchmark runs, metrics are stored as structured dictionaries, and CSV writing happens after the request phase rather than inside the hot path. For higher-concurrency or distributed tests, I would monitor the load-generator host separately and compare its CPU, memory, network, and event-loop overhead against the Ollama host metrics to verify that the harness is not the limiting component. If the load generator becomes saturated, I would move to multiple load-generator nodes or a dedicated benchmark runner separate from the Ollama server.

---

## contents

1. technology choices

2. file structure

3. workload model

4. metrics collected

5. bottleneck identification

6. local vs distributed monitoring assumption

7. scalability considerations

8. limitations

9. how to run

10. output files

---

## 1. technology choices

**Python:** Python was chosen because it enables fast PoC development, has strong support for async HTTP clients, and provides mature system-monitoring libraries.

**asyncio + httpx:** Used to simulate concurrent users with non-blocking HTTP requests.

**Ollama HTTP API:** The direct HTTP API is used instead of an SDK because the harness needs access to streamed response chunks. This is required to measure TTFT separately from total request latency.

**psutil:** Used for CPU, memory, and disk metrics.

**nvidia-smi:** Used for NVIDIA GPU utilization, VRAM usage, and temperature.

**CSV:** Used because it is simple, inspectable, and easy to analyze later.

---

## 2. file structure

| File | Responsibility |
| - | - |
| `src/main.py` | Benchmark orchestration: starts monitoring, launches concurrent user tasks, writes outputs |
| `src/client.py` | Sends streaming requests to Ollama and records client-side metrics |
| `src/workloads.py` | Defines workload profiles for short/long prompts and completions |
| `src/monitoring.py` | Samples host CPU, memory, disk, GPU, and VRAM metrics |
| `src/results.py` | Writes structured benchmark results to CSV |
| `src/config.py` | Reads runtime configuration from environment variables |
| `env.sh` | Defines Ollama and benchmark environment variables |
| `setup.sh` | Creates the virtual environment and installs dependencies |
| `run.sh` | Loads environment variables and runs the benchmark |

---

## 3. workload model

*Prompt length is used to stress prompt evaluation/prefill.*

*`num_predict` is used to control expected output length and stress sustained token generation.*

| Workload | Purpose |
| - | - |
| `short_prompt_short_output` | Baseline latency |
| `short_prompt_long_output` | Generation throughput pressure |
| `long_prompt_short_output` | Prompt/prefill pressure |
| `long_prompt_long_output` | Combined long input and long generation |


*The selected workload is currently chosen in `src/main.py` from the profiles defined in `src/workloads.py`. A future improvement would expose the workload name as an environment variable or CLI argument.*

```python  
workload = WORKLOADS["short_prompt_short_output"]  
```

---

## 4. metrics collected

### Client/request metrics

These are measured by the load generator:

- `client_ttft_ns`

- `client_total_latency_ns`

- `client_tps`

- success/failure status

- RPS, calculated at the run level

TTFT is measured from the client request start until the first non-empty streamed response chunk is received.

### Host/resource metrics

These are sampled from the monitored host:

- `host_cpu_percent`

- `host_memory_used_mb`

- `host_memory_percent`

- `host_disk_read_mb_total`

- `host_disk_write_mb_total`

- `host_gpu_util_percent`

- `host_vram_used_mb`

- `host_vram_total_mb`

- `host_gpu_temperature`

---

## 5. bottleneck identification

In an observed 5-user run on the local test machine, long-output workloads showed a staircase TTFT pattern while client TPS stayed around 47–48 tokens/s. GPU utilization reached about 96–97%, CPU stayed low, and VRAM remained stable around 5.36 GB out of 8.19 GB. This suggests backend queueing plus GPU compute pressure, not VRAM exhaustion.

| Signal | Likely interpretation |
| - | - |
| High `client_ttft_ns`, stable `client_tps` | Queueing / serialized inference |
| High `host_gpu_util_percent`, VRAM below limit | GPU compute saturation |
| VRAM near total + failures/timeouts | VRAM exhaustion |
| High CPU + low GPU | CPU-side bottleneck |
| Low CPU/GPU + high latency | client/network/server queueing issue |
| Disk counters increase sharply | model loading, paging, or I/O pressure |


The harness avoids printing streamed tokens during benchmark runs and writes structured results to files to reduce client-side overhead. For larger tests, the load-generator machine should also be monitored to ensure the harness itself is not the bottleneck.

---

## 6. local vs distributed monitoring assumption

This PoC currently uses `MONITORING_SCOPE=ollama_host_local`, meaning the harness and Ollama are assumed to run on the same host. Under this constraint, local `psutil` and `nvidia-smi` metrics describe the same machine serving inference.

This assumption does not hold if the harness runs on a separate load-generator machine. In that case, local host metrics would describe the harness machine, not the Ollama server. For distributed testing, host metrics should come from the Ollama host through a monitoring agent, Prometheus/node exporter, NVIDIA DCGM exporter, SSH-based collector, or another remote source.

The client-side request metrics remain valid from the harness perspective, but host-side resource metrics need a separate source of truth.

---

## 7. scalability considerations

*The harness should not become the bottleneck. For higher concurrency, I would monitor the load generator itself and distribute load generation if client CPU, network, or event-loop overhead becomes significant.*

- avoid printing streamed tokens during benchmark runs

- write structured metrics instead of terminal output

- add timeouts and failure classification

- consider multiple load-generator machines if the harness becomes the bottleneck

- monitor load-generator CPU separately from Ollama host CPU in distributed tests

---

## 8. limitations

- Workload selection is currently changed in code rather than through CLI or environment configuration.

- The current writer assumes non-empty result lists.

- Error handling is minimal; HTTP failures or timeouts should be classified more explicitly in a production version.

- Host metrics are sampled every second, which may miss short GPU spikes in very short workloads.

- The GPU monitor optionally requires `nvidia-smi`. If unavailable, GPU fields are recorded as null values

- Although the core project supports any OS, the automated bash scripts: `setup.sh`, `env.sh` and `run.sh` are designed for Linux. For other operating systems, such as Windows or macOS, consider executing the equivalent setup and run steps manually.

---

## 9. how to run

*The benchmark configuration is provided through environment variables in `env.sh`, including the Ollama API URL, selected model, number of simulated users, host identifier, and monitoring scope.*

execution of project:

1. Ensure Ollama is installed and running.

2. Ensure the selected model is available, for example `llama3.1:8b`.

3. Edit `env.sh` to configure the model, user count, API URL, and monitoring scope.

4. Run setup once:  
  
```bash  
./setup.sh  
```  
  
5. Run the benchmark:  
  
```bash  
./run.sh  
```  
  
6. Inspect the generated CSV files in the `output/` directory.

---

## 10. output Files

The harness writes two CSV files to the `output/` directory:

| File | Description |
| - | - |
| `output/client_metrics.csv` | One row per simulated user request, including TTFT, total latency, TPS, success status, model, and workload metadata |
| `output/host_metrics.csv` | One row per resource-monitoring sample, including CPU, memory, disk, GPU, VRAM, host ID, and monitoring scope |

