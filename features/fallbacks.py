from telegram.ext import CallbackQueryHandler, CommandHandler

def get_fallbacks() -> list:
    """
    Xây dựng và trả về danh sách các handler dự phòng (fallback).
    Import được thực hiện bên trong hàm để tránh circular import.
    """
    from .common_handlers import show_promo_menu, show_main_menu, unified_cleanup_handler, show_transaction_menu
    #from .promo_handlers.kl001 import start_kl001
    #from .promo_handlers.kl006 import start_kl006
    #from .promo_handlers.kl007 import start_kl007
    #from .promo_handlers.app_promo import start_app_promo
    #from .promo_handlers.sharing import share_code_entry_point
    #from .transaction_handlers.deposit import start_deposit_flow
    #from .transaction_handlers.withdraw import start_withdraw_flow

    # Trả về danh sách handler đã xây dựng
    return [

        CallbackQueryHandler(unified_cleanup_handler, pattern='^cleanup_now$'),
        CallbackQueryHandler(show_main_menu, pattern='^show_main_menu$'),
        CallbackQueryHandler(show_promo_menu, pattern='^show_promo_menu$'),
        CallbackQueryHandler(show_transaction_menu, pattern='^show_transaction_menu$')
    ]