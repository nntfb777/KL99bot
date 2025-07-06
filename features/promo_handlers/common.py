# features/promo_handlers/common.py

from telegram.ext import CallbackQueryHandler, CommandHandler
# Import các hàm xử lý từ features.common_handlers
from ..common_handlers import show_promo_menu, show_main_menu, cancel

# Danh sách các handler dự phòng (fallback) dùng chung
# Đảm bảo chứa tất cả các hành động "thoát"
PROMO_FALLBACKS = [
    CallbackQueryHandler(show_main_menu, pattern='^back_to_main_menu$'),
    CallbackQueryHandler(show_promo_menu, pattern='^show_promo_menu$'),
    CallbackQueryHandler(cancel, pattern='^cancel$'),
    CommandHandler("cancel", cancel),
]