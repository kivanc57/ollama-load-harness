import asyncio
import httpx
import json

URL= "http://localhost:11434/api/generate"

MODEL = "llama3.1:8b"
MODEL2 = "gemma3:4b"
PROMPT = 'what is 2 x 2 = ?'

async def chat(client, model, prompt):

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
    }

    async with client.stream("POST", URL, json=payload) as response:
        response.raise_for_status()

        async for line in response.aiter_lines():
            if not line:
                continue

            data = json.loads(line)

            if "response" in data:
                print(data["response"], end="", flush=True)

            if data.get("done"):
                print()
                break

async def main():
    async with httpx.AsyncClient(timeout=None) as client:
        await chat(client, MODEL, PROMPT)

if __name__ == "__main__":
    asyncio.run(main())

