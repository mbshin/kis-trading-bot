from __future__ import annotations
import httpx

async def notify(webhook_url: str, text: str):
    if not webhook_url:
        return
    async with httpx.AsyncClient(timeout=5) as client:
        await client.post(webhook_url, json={"text": text})
