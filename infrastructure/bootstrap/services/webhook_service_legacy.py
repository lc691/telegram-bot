import asyncio
import httpx
from typing import Optional

from configs.logging_setup import log


TELEGRAM_API = "https://api.telegram.org"

"""
LEGACY FILE
Telegram webhook (Railway-era)
NOT USED in VPS polling-only mode
"""


async def register_webhook_legacy(
    token: str,
    url: str,
    *,
    secret_token: Optional[str] = None,
    max_retry: int = 5,
    drop_pending_updates: bool = True,
) -> bool:
    """
    VPS-safe Telegram webhook registration
    """

    api_info = f"{TELEGRAM_API}/bot{token}/getWebhookInfo"
    api_set = f"{TELEGRAM_API}/bot{token}/setWebhook"

    timeout = httpx.Timeout(
        connect=5.0,
        read=20.0,
        write=5.0,
        pool=5.0,
    )

    payload = {
        "url": url,
        "drop_pending_updates": drop_pending_updates,
    }

    if secret_token:
        payload["secret_token"] = secret_token

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, max_retry + 1):
            try:
                info = await client.get(api_info)
                if info.status_code == 200:
                    current = info.json().get("result", {}).get("url", "")
                    if current == url:
                        log.info("Webhook already set: %s", url)
                        return True

                res = await client.post(api_set, json=payload)
                data = res.json()

                if res.status_code == 200 and data.get("ok"):
                    log.info("Webhook registered: %s", url)
                    return True

                if res.status_code == 429:
                    retry_after = data.get("parameters", {}).get("retry_after", 1)
                    log.warning("Webhook rate limited, retry in %s", retry_after)
                    await asyncio.sleep(retry_after)
                    continue

                log.warning(
                    "Webhook failed (%s/%s): %s",
                    attempt,
                    max_retry,
                    data,
                )

            except httpx.RequestError as e:
                log.warning(
                    "Webhook network error (%s/%s): %s",
                    attempt,
                    max_retry,
                    e,
                )
            except Exception:
                log.exception(
                    "Unexpected webhook error (%s/%s)",
                    attempt,
                    max_retry,
                )

            await asyncio.sleep(min(2**attempt, 30))

    log.critical("Webhook registration failed")
    return False
