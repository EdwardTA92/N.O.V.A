from fastapi import FastAPI
from pydantic import BaseModel
from openrouter import OpenRouter   # Imported from openrouter-sdk
import os

app = FastAPI()

class UserPrompt(BaseModel):
    prompt: str

@app.post("/plan")
async def plan(inp: UserPrompt):
    router = OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY"))
    sys_msg = (
        "You are PlannerAI. Return ONLY valid JSON with schema: "
        "{ domains: string[], tasks: { [domain:string]: "
        "{ subtasks:string[], tools:string[] } } }"
    )
    llm_resp = await router.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{"role":"system","content":sys_msg},
                  {"role":"user","content":inp.prompt}],
        response_format="json"
    )
    return llm_resp
