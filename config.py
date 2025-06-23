# Tệp: config.py
import os



BOT_TOKEN = os.getenv('BOT_TOKEN', '7870846131:AAHqO06C8knRCb1JlvlDzBSXRQolgHUVrPk')

# Các liên kết chính của bot
APP_DOWNLOAD_LINK = 'https://99kl.app/DownloadApp/'
GAME_LINK = 'https://kl99.immo/'
TELEGRAM_CHANNEL_LINK = 'https://t.me/bet_kl99'
FACEBOOK_LINK = 'https://www.facebook.com/KL99GiaiTriDinhCaoChauA/'
CSKH_LINK = 'https://umyq3uemgd.we2vub70.com/chatwindow.aspx?siteId=65002300&planId=88c557f5-5a2c-4ea3-b364-9cda2464fa7b&chatgroup=3&_=1748177033765'

# Cấu hình Database
DATABASE_FILE = "klbot.db"

# Tên người dùng của bot (sẽ được cập nhật tự động khi bot khởi tạo từ Telegram API)
BOT_USERNAME = 'KL99OfficialBot'

# Các mốc chia sẻ và số tiền thưởng
SHARE_MILESTONES = [15, 30, 50, 100]

# Bạn có thể lấy File ID bằng cách gửi ảnh cho bot và dùng lệnh /getid (nếu bạn đã implement)
# hoặc dùng hàm get_file_id_handler trong handlers/utils.py
START_IMAGE_FILE_ID = "AgACAgUAAxkBAAICg2g-Mt3D4jR3CW2HjTB9pvt-B2GjAAK2wTEbhgHwVaax8wABZYXQngEAAwIAA3MAAzYE"

# (Sử dụng lệnh /id trong nhóm admin để lấy ID chính xác)
ID_GROUP_PROMO = -4807889335 # Ví dụ: ID nhóm admin/kiểm duyệt của bạn
