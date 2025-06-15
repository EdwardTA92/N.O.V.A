import os
import time
import tempfile
import shutil
import requests
import redis
import docker

SYSTEM_PROMPT = "Write FastAPI code that exposes MCP tool using fastapi-mcp"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
STREAM_KEY = "connector:req"
CONNECTOR_HASH = "connectors"


def generate_code(spec_json: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "model": "openrouter/gpt-4o",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": spec_json},
        ],
    }
    resp = requests.post(OPENROUTER_URL, headers=headers, json=data)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def build_and_run(tool_name: str, code: str) -> str:
    client = docker.from_env()
    work_dir = tempfile.mkdtemp()
    code_path = os.path.join("/tmp", f"{tool_name}.py")
    with open(code_path, "w") as f:
        f.write(code)
    shutil.copy(code_path, os.path.join(work_dir, "main.py"))
    dockerfile = """FROM python:3.11-slim
WORKDIR /app
COPY main.py /app/main.py
RUN pip install fastapi fastapi-mcp uvicorn
CMD [\"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]
"""
    with open(os.path.join(work_dir, "Dockerfile"), "w") as f:
        f.write(dockerfile)
    image, _ = client.images.build(path=work_dir, tag=f"{tool_name}:latest")
    container = client.containers.run(image.id, detach=True, ports={'8000/tcp': None})
    # wait for container to be ready
    for _ in range(30):
        container.reload()
        port_info = container.attrs.get("NetworkSettings", {}).get("Ports", {})
        host_port = None
        if port_info.get('8000/tcp'):
            host_port = port_info['8000/tcp'][0]['HostPort']
        if host_port:
            try:
                r = requests.get(f"http://localhost:{host_port}/health")
                if r.status_code == 200:
                    return f"http://localhost:{host_port}"
            except Exception:
                pass
        time.sleep(1)
    raise RuntimeError("container failed health check")


def main():
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), decode_responses=True)
    last_id = '$'
    while True:
        resp = r.xread({STREAM_KEY: last_id}, block=0)
        for stream, messages in resp:
            for msg_id, data in messages:
                last_id = msg_id
                tool_name = data.get('tool_name')
                spec_json = data.get('spec_json')
                if not tool_name or not spec_json:
                    continue
                code = generate_code(spec_json)
                url = build_and_run(tool_name, code)
                r.hset(CONNECTOR_HASH, tool_name, url)


if __name__ == "__main__":
    main()
