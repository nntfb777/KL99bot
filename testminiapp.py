from telegram import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler

# Thay thế bằng token bot của bạn
BOT_TOKEN = "7968751709:AAEXG1AZQoKhzrNEIeW6dsyQ5Utd-3bSpAA"

async def start(update, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Mở ứng dụng", web_app=WebAppInfo(url="https://99kl.games/Mobile"))]
    ])
    await update.message.reply_text(
        "Cảm ơn quý hội viên đã tin tưởng và đồng hành cùng KL999\n Hãy thường xuyên theo dõi kênh để nhận CODE mỗi ngày nhé!",
        reply_markup=keyboard
    )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == '__main__':
    main()