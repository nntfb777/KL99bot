# utils/decorators.py
import logging
import functools
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from utils import analytics

logger = logging.getLogger(__name__)

def log_callback_query(func):
    """
    Decorator "vẹn cả đôi đường":
    1. Trả lời query ngay lập tức để có phản hồi nhanh nhất.
    2. Sử dụng cơ chế khóa để chống double-click một cách tuyệt đối.
    3. Chạy handler gốc.
    4. Ghi log và gửi analytics ở chế độ nền.
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.callback_query:
            return await func(update, context, *args, **kwargs)

        query = update.callback_query
        user = query.from_user

        # BƯỚC 1: TRẢ LỜI QUERY NGAY LẬP TỨC (Ưu tiên tốc độ)
        try:
            await query.answer()
        except BadRequest as e:
            if "Query is too old" in str(e):
                logger.warning(f"Decorator ignored 'Query is too old' for '{query.data}'.")
                return # Dừng hẳn nếu query đã hết hạn
            else:
                raise e

        # BƯỚC 2: KHÓA ĐỂ CHỐNG DOUBLE-CLICK (Ưu tiên an toàn)
        lock_key = f"query_lock_{query.id}"
        if context.chat_data.get(lock_key):
            logger.warning(f"Decorator blocked duplicate execution for query_id '{query.id}'.")
            return # Dừng hẳn nếu đã bị khóa
        
        context.chat_data[lock_key] = True

        try:
            # BƯỚC 3: CHẠY HANDLER GỐC (Ưu tiên người dùng)
            result = await func(update, context, *args, **kwargs)

            # BƯỚC 4: CÁC TÁC VỤ NỀN (Chạy sau)
            logger.info(
                f"Execution SUCCEEDED for '{func.__name__}' (callback: '{query.data}')"
            )
            asyncio.create_task(
                analytics.log_event(
                    user_id=user.id,
                    event_name='button_click',
                    params={'callback_data': query.data}
                )
            )
            
            return result

        except Exception as e:
            logger.error(
                f"Execution FAILED for '{func.__name__}' (callback: '{query.data}'). Error: {e}",
                exc_info=True
            )
            raise e

        finally:
            # BƯỚC 5: LUÔN MỞ KHÓA
            context.chat_data.pop(lock_key, None)
    
    return wrapper