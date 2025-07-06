# core/telegram_logger.py

import logging
import html
from telegram.ext import Application
from telegram.constants import ParseMode

class TelegramLogHandler(logging.Handler):
    """
    Một logging handler tùy chỉnh để gửi log đến Telegram thông qua Application.
    """
    def __init__(self, application: Application, chat_id: int):
        super().__init__()
        self.application = application
        self.chat_id = chat_id

    def emit(self, record: logging.LogRecord):
        # Nếu không có application hoặc chat_id, không làm gì cả
        if not self.application or not self.chat_id:
            return

        # Lấy bot từ application
        bot = self.application.bot

        log_entry = self.format(record)
        escaped_log_entry = html.escape(log_entry)
        
        max_len = 4096
        if len(escaped_log_entry) > max_len:
            escaped_log_entry = escaped_log_entry[:max_len-10] + "\n\n[...]"
        
        # Sử dụng job_queue để chạy hàm gửi tin nhắn một cách an toàn
        self.application.job_queue.run_once(
            self.send_log_message,
            when=0, # Chạy ngay lập tức
            data={'bot': bot, 'text': f"<code>{escaped_log_entry}</code>"}
        )

    async def send_log_message(self, context):
        """Hàm callback bất đồng bộ được thực thi bởi JobQueue."""
        job_data = context.job.data
        bot = job_data['bot']
        text = job_data['text']
        try:
            await bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=ParseMode.HTML
            )
        except Exception:
            # Nếu việc gửi log bị lỗi, in ra console
            print("--- LỖI GỬI LOG ĐẾN TELEGRAM ---")
            print(text)
            print("---------------------------------")