import asyncio
import json

from apps.api.app.main import app


def call_asgi_app(path: str) -> tuple[int, dict[str, str]]:
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "scheme": "http",
    }

    asyncio.run(app(scope, receive, send))

    response_start = next(message for message in messages if message["type"] == "http.response.start")
    response_body = next(message for message in messages if message["type"] == "http.response.body")
    return response_start["status"], json.loads(response_body["body"])


def test_health():
    status_code, body = call_asgi_app("/health")

    assert status_code == 200
    assert body == {"status": "UP"}
