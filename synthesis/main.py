import os
from fastapi import FastAPI, HTTPException
import redis.asyncio as redis
from openai import AsyncOpenAI

app = FastAPI(title="Synthesis Service")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def build_prompt(events: list[str]) -> str:
    joined = "\n".join(events)
    return (
        "Summarize the following events into a concise markdown report. "
        "Highlight any novel ideas with a bullet starting with the 🧬 emoji. "
        "Finish with a '### References' section listing any sources or notes.\n" 
        f"Events:\n{joined}"
    )


async def generate_report(events: list[str]) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = AsyncOpenAI(api_key=api_key)
    prompt = build_prompt(events)
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


@app.post("/synthesize/{run_id}")
async def synthesize(run_id: str):
    key = f"run:{run_id}:events"
    events = await redis_client.lrange(key, 0, -1)
    if not events:
        raise HTTPException(status_code=404, detail="No events found")
    markdown = await generate_report(events)
    return {"markdown": markdown}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
