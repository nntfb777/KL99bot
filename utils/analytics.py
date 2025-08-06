# utils/analytics.py
import httpx 
import logging
import uuid
import config 

logger = logging.getLogger(__name__)

GA4_URL = "https://www.google-analytics.com/mp/collect"


async def log_event(user_id: int, event_name: str, params: dict = None):
    """
    (Async) Gửi một sự kiện đến Google Analytics 4.
    """
    if not config.GA4_MEASUREMENT_ID or not config.GA4_API_SECRET:
        # Giữ nguyên logic kiểm tra config
        logger.debug("GA4 chưa được cấu hình, bỏ qua việc gửi event.")
        return

    client_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(user_id)))

    event_payload = {
        'name': event_name,
        'params': params or {}
    }
    event_payload['params']['telegram_user_id'] = user_id

    request_body = {
        'client_id': client_id,
        'events': [event_payload]
    }

    # <<--- SỬ DỤNG `httpx.AsyncClient` ---
    try:
        # `async with` sẽ tự động quản lý client và kết nối
        async with httpx.AsyncClient() as client:
            # Gửi request bất đồng bộ bằng `await client.post()`
            response = await client.post(
                f"{GA4_URL}?api_secret={config.GA4_API_SECRET}&measurement_id={config.GA4_MEASUREMENT_ID}",
                json=request_body,
                timeout=5.0 # Timeout vẫn rất quan trọng
            )

            if response.status_code != 204:
                logger.warning(f"Lỗi khi gửi sự kiện đến GA4: Status {response.status_code}, Response: {response.text}")

    except httpx.RequestError as e:
        logger.error(f"Lỗi kết nối khi gửi sự kiện đến GA4: {e}")
    except Exception as e:
        logger.error(f"Lỗi không xác định khi gửi sự kiện đến GA4: {e}", exc_info=True)