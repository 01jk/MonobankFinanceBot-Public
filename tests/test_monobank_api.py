import pytest
import time
from src.services.monobank_api import MonobankClient, MonobankRateLimitError

@pytest.mark.asyncio
async def test_rate_limit_check():
    client = MonobankClient()
    token = "test_token_123"
    client._last_request_time[token] = time.time()
    
    with pytest.raises(MonobankRateLimitError):
        await client._check_rate_limit(token)
