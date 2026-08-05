import asyncio
import time
import aiohttp
from typing import Dict, Any, Optional

class MonobankRateLimitError(Exception):
    pass

class MonobankClient:
    def __init__(self, base_url: str = "https://api.monobank.ua"):
        self.base_url = base_url
        self._last_request_time: Dict[str, float] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, token: str) -> asyncio.Lock:
        if token not in self._locks:
            self._locks[token] = asyncio.Lock()
        return self._locks[token]

    async def _check_rate_limit(self, token: str):
        last_time = self._last_request_time.get(token, 0)
        elapsed = time.time() - last_time
        if elapsed < 60:
            raise MonobankRateLimitError(f"Rate limit exceeded. Wait {int(60 - elapsed)}s.")

    async def get_client_info(self, token: str) -> Dict[str, Any]:
        async with self._get_lock(token):
            await self._check_rate_limit(token)
            headers = {"X-Token": token}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/personal/client-info", headers=headers) as resp:
                    self._last_request_time[token] = time.time()
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 429:
                        raise MonobankRateLimitError("Monobank API 429 Too Many Requests")
                    else:
                        text = await resp.text()
                        raise Exception(f"Monobank API error {resp.status}: {text}")

    async def get_statement(self, token: str, account: str, from_ts: int, to_ts: Optional[int] = None) -> list:
        async with self._get_lock(token):
            await self._check_rate_limit(token)
            headers = {"X-Token": token}
            url = f"{self.base_url}/personal/statement/{account}/{from_ts}"
            if to_ts:
                url += f"/{to_ts}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    self._last_request_time[token] = time.time()
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 429:
                        raise MonobankRateLimitError("Monobank API 429 Too Many Requests")
                    else:
                        text = await resp.text()
                        raise Exception(f"Monobank API error {resp.status}: {text}")

    async def set_webhook(self, token: str, webhook_url: str) -> bool:
        headers = {"X-Token": token}
        payload = {"webHookUrl": webhook_url}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/personal/webhook", headers=headers, json=payload) as resp:
                return resp.status == 200
