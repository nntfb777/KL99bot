import datetime
import pytz

# Định dạng ngày hôm qua theo múi giờ UTC-4
now_utc = datetime.datetime.now(pytz.utc)
utc_minus_4_timezone = pytz.timezone('Etc/GMT+4') # Corresponds to AST (e.g., Atlantic Time, Manaus)

# Using the original UTC-4 logic from your file
now_utc_minus_4 = now_utc.astimezone(utc_minus_4_timezone)
yesterday_utc_minus_4 = now_utc_minus_4 - datetime.timedelta(days=1)
YESTERDAY_DMY = yesterday_utc_minus_4.strftime('%d/%m/%Y')

# --- NỘI DUNG KHUYẾN MÃI (KHÔI PHỤC TỪ FILE GỐC CỦA BẠN) ---
# Đã thêm ký tự `\` để sửa lỗi parse markdown, không thay đổi nội dung.
PROMO_TEXT_KL001 = (
    "Quý khách vui lòng tham khảo điều kiện khuyến mãi 𝐊𝐋𝟎𝟎𝟏 thành viên mới nạp tiền lần đầu 𝟏𝟗𝟗𝐊 tặng thưởng 𝟏𝟗𝟗𝐊:\\n"
    "1\\\\. Chương trình này chỉ áp dụng cho tất cả các thành viên mới của 𝐊𝐋𝟗𝟗 và chỉ được nhận một lần duy nhất khi nạp tiền lần đầu\\\\.\\n"
    "2\\\\. Số tiền nạp tối thiểu để nhận khuyến mãi này là 𝟏𝟗𝟗K\\\\.\\n"
    "3\\\\. Số tiền thưởng là 𝟏𝟗𝟗K\\\\.\\n"
    "4\\\\. Khuyến mãi yêu cầu 𝟑 vòng cược\\\\.\\n"
    "5\\\\. Thành viên cần cung cấp ảnh chụp hóa đơn nạp tiền và ảnh chụp tài khoản game cho CSKH\\\\.\\n"
    "6\\\\. Nếu thành viên hủy khuyến mãi sau khi nhận, số tiền thưởng và lợi nhuận phát sinh sẽ bị khấu trừ\\\\.\\n"
    "7\\\\. Nếu thành viên có bất kỳ hành vi lạm dụng hoặc gian lận nào, 𝐊𝐋𝟗𝟗 có quyền hủy bỏ tất cả các khuyến mãi và đóng băng tài khoản\\\\.\\n"
    "8\\\\. Quyền giải thích cuối cùng thuộc về 𝐊𝐋𝟗𝟗\\\\.\n"
    "\\n"
    "🎁 Nhấn *\"Nhận ngay\"* bên dưới để yêu cầu khuyến mãi và cung cấp thông tin cho CSKH\\."
)

PROMO_TEXT_KL006 = (
    "Chào mừng bạn đến với chương trình khuyến mãi *KL006 - Thưởng nhóm người dùng* của KL99!\\n"
    "\\n"
    "👥 *Thành viên: 5 người*\\n"
    "🎁 *Thưởng:* 100K VND\\n"
    "📝 *Điều kiện: *\\n"
    "1\\\\. Tất cả thành viên trong nhóm phải là người chơi mới đăng ký và nạp tiền lần đầu tại KL99\\\\.\\n"
    "2\\\\. Mỗi thành viên cần nạp tối thiểu 200K VND\\\\.\\n"
    "3\\\\. Mỗi nhóm chỉ được nhận thưởng một lần\\\\.\\n"
    "4\\\\. Liên hệ CSKH sau khi hoàn thành các điều kiện để nhận thưởng\\\\.\n"
    "\\n"
    "👥 *Thành viên: 10 người*\\n"
    "🎁 *Thưởng:* 300K VND\\n"
    "📝 *Điều kiện: *\\n"
    "1\\\\. Tất cả thành viên trong nhóm phải là người chơi mới đăng ký và nạp tiền lần đầu tại KL99\\\\.\\n"
    "2\\\\. Mỗi thành viên cần nạp tối thiểu 200K VND\\\\.\\n"
    "3\\\\. Mỗi nhóm chỉ được nhận thưởng một lần\\\\.\\n"
    "4\\\\. Liên hệ CSKH sau khi hoàn thành các điều kiện để nhận thưởng\\\\.\n"
    "\\n"
    "🎁 Nhấn *\"Nhận ngay\"* bên dưới để yêu cầu khuyến mãi và cung cấp thông tin cho CSKH\\."
)

PROMO_TEXT_KL007 = (
    "Chào mừng bạn đến với chương trình khuyến mãi *KL007 - Hoàn trả hàng ngày lên đến 1%* của KL99!\\n"
    "\\n"
    "📅 *Thời gian:* Hàng ngày\\n"
    "💸 *Tỷ lệ hoàn trả:* Lên đến 1% dựa trên tổng số tiền cược hợp lệ hàng ngày của bạn\\n"
    "\\n"
    "📝 *Điều kiện:*\\n"
    "1\\\\. Hoàn trả được tính dựa trên tổng số tiền cược hợp lệ của tất cả các trò chơi trong ngày hôm trước \\({YESTERDAY_DMY}\\)\\\\.\\n"
    "2\\\\. Tiền hoàn trả sẽ được cập nhật vào tài khoản của bạn hàng ngày, chậm nhất vào 12:00 trưa (GMT+7) ngày hôm sau\\\\.\\n"
    "3\\\\. Không có yêu cầu vòng cược đối với tiền hoàn trả\\\\.\\n"
    "4\\\\. Chương trình này áp dụng cho tất cả các thành viên của KL99\\\\.\\n"
    "5\\\\. KL99 có quyền thay đổi hoặc chấm dứt chương trình này bất cứ lúc nào mà không cần thông báo trước\\\\.\\n"
    "6\\\\. Quyền giải thích cuối cùng thuộc về KL99\\\\.\n"
    "\\n"
    "🎁 Nhấn *\"Nhận ngay\"* bên dưới để yêu cầu khuyến mãi và cung cấp thông tin cho CSKH\\."
)

PROMO_TEXT_APP_PROMO = (
    "Tham gia chương trình *\"Tải App Nhận Quà\"* để nhận thưởng đặc biệt từ KL99!\\n"
    "\\n"
    "📱 *Cách nhận thưởng:*\\n"
    "1\\\\. Tải và cài đặt ứng dụng KL99 trên điện thoại của bạn\\\\.\\n"
    "2\\\\. Đăng nhập vào ứng dụng và chụp ảnh màn hình giao diện chính\\\\.\\n"
    "3\\\\. Gửi ảnh chụp màn hình đó kèm theo username của bạn cho chúng tôi để xác nhận\\\\.\n"
    "\\n"
    "🎁 *Phần thưởng:* Ngay lập tức nhận 50K VND vào tài khoản của bạn!\\n"
    "\\n"
    "📝 *Lưu ý:*\\n"
    "1\\\\. Chương trình chỉ áp dụng cho thành viên mới lần đầu tải và đăng nhập ứng dụng\\\\.\\n"
    "2\\\\. Mỗi tài khoản chỉ được nhận thưởng một lần duy nhất\\\\.\\n"
    "3\\\\. Yêu cầu 1 vòng cược để rút tiền thưởng\\\\.\\n"
    "4\\\\. Mọi hành vi gian lận sẽ bị xử lý nghiêm\\\\.\\n"
    "5\\\\. KL99 có quyền thay đổi hoặc chấm dứt chương trình này bất cứ lúc nào\\\\.\\n"
    "6\\\\. Quyền giải thích cuối cùng thuộc về KL99\\\\.\n"
    "\\n"
    "🎁 Nhấn *\"Nhận ngay\"* bên dưới để yêu cầu khuyến mãi và cung cấp thông tin cho CSKH\\."
)

RESPONSE_MESSAGES = {
    # General
    "welcome_message": "Chào mừng bạn đến với KL99 Official Bot!",
    "main_menu_text": "Chào mừng bạn trở lại menu chính. Bạn muốn làm gì hôm nay?",
    "invalid_command": "Lệnh không hợp lệ. Vui lòng sử dụng các lệnh có sẵn hoặc chọn từ menu.",
    "error_processing_request": "Đã xảy ra lỗi trong quá trình xử lý yêu cầu của bạn. Vui lòng thử lại sau.",
    "request_cancelled": "Yêu cầu của bạn đã được hủy bỏ.",
    "yeu_cau_dang_xu_ly": "✅ Yêu cầu của bạn đã được gửi và đang chờ xử lý. Vui lòng đợi thông báo từ admin.",
    "error_sending_request": "Đã xảy ra lỗi khi gửi yêu cầu của bạn. Vui lòng thử lại.",
    "invalid_input": "Đầu vào không hợp lệ. Vui lòng thử lại.",

    # --- BUTTON TEXTS MENU CHÍNH ---
    "deposit_button_text": "💰 Nạp Tiền",
    "withdrawal_button_text": "💸 Rút Tiền",
    "promo_button_text": "🎁 Khuyến Mãi",
    "share_code_button_text": "🔗 Chia Sẻ",
    "facebook_button_text": "🌐 Facebook",
    "telegram_channel_button_text": "📢 Kênh Telegram",
    "cskh_button_text": "👩‍💻 CSKH",
    "download_app_button_text": "📱 Tải App",
    "homepage_button_text": "🏠 Trang Chủ",

    # --- BUTTON TEXTS MENU KHUYẾN MÃI (MỚI THÊM HOẶC SỬA) ---
    "promo_kl001_button": "🎁 KL001 - Nạp 199K Tặng 199K",
    "promo_kl006_button": "👥 KL006 - Thưởng Nhóm",
    "promo_kl007_button": "💸 KL007 - Hoàn Trả Hàng Ngày",
    "promo_app_promo_button": "📱 Tải App Nhận Quà",
    "back_to_menu_button": "⬅️ Quay Lại Menu Chính",
    "agree_button_text": "✅ Đồng Ý", #
    "back_to_promo_menu_button_text": "⬅️ Quay Lại Menu Khuyến Mãi", # Nút quay lại menu khuyến mãi
    
        # Tin nhắn hỏi thông tin sau khi đồng ý khuyến mãi
    "ask_username_kl001_after_agree": "Vui lòng nhập *TÊN TÀI KHOẢN GAME* của bạn để yêu cầu khuyến mãi KL001:",
    "ask_group_size_kl006": "Vui lòng nhập *SỐ LƯỢNG THÀNH VIÊN* trong nhóm của bạn (ví dụ: 5 hoặc 10):",
    "ask_username_kl007_after_agree": "Vui lòng nhập *TÊN TÀI KHOẢN GAME* của bạn để yêu cầu hoàn trả KL007:",
    "app_promo_ask_username": "Vui lòng nhập *TÊN TÀI KHOẢN GAME* của bạn để yêu cầu khuyến mãi ứng dụng:",
    "app_promo_ask_image": "Tuyệt vời! Bây giờ, vui lòng gửi *ảnh chụp màn hình* bạn đã tải và đăng nhập ứng dụng.",

    # Lỗi nhập liệu và tin nhắn trạng thái
    "invalid_group_size": "Số lượng thành viên không hợp lệ. Vui lòng nhập một số nguyên dương.",
    "invalid_username_format_kl006": "Định dạng tên tài khoản không hợp lệ. Vui lòng nhập mỗi tên trên một dòng riêng biệt.",
    "kl006_awaiting_approval": "✅ Yêu cầu KL006 của nhóm bạn đã được gửi và đang chờ xử lý. Vui lòng đợi thông báo từ admin.",
    "no_image_provided": "Bạn chưa gửi ảnh. Vui lòng gửi ảnh chụp màn hình ứng dụng.",
    
    
    # Deposit
    "deposit_ask_username": "Vui lòng nhập *TÊN TÀI KHOẢN GAME* của bạn để thực hiện nạp tiền:",
    "deposit_ask_image": "Tuyệt vời! Bây giờ, vui lòng gửi *ảnh chụp hóa đơn* hoặc *bill chuyển khoản* của bạn.",
    "deposit_processing": "Đang xử lý yêu cầu nạp tiền của bạn. Vui lòng đợi trong giây lát...",
    "deposit_received_admin_notify": "💰 *YÊU CẦU NẠP TIỀN MỚI* 💰\\n\\n👤 Khách: {user_mention} `({user.id})`\\n🎮 Tên game: `{game_username}`",
    "deposit_approved": "✅ Yêu cầu nạp tiền {amount} của bạn đã được duyệt thành công!",
    "deposit_rejected_failed_transfer": "❌ Yêu cầu nạp tiền của bạn bị từ chối: Chuyển khoản thất bại. Vui lòng kiểm tra lại và thử lại.",
    "deposit_rejected_wrong_amount": "❌ Yêu cầu nạp tiền của bạn bị từ chối: Sai số tiền. Vui lòng kiểm tra lại và thử lại.",
    "deposit_rejected_no_transfer": "❌ Yêu cầu nạp tiền của bạn bị từ chối: Không có chuyển khoản được tìm thấy. Vui lòng liên hệ CSKH.",
    "deposit_rejected_duplicate_receipt": "❌ Yêu cầu nạp tiền của bạn bị từ chối: Bill chuyển khoản này đã được sử dụng. Vui lòng liên hệ CSKH.",
    "deposit_rejected_generic": "❌ Yêu cầu nạp tiền của bạn bị từ chối: Lý do khác. Vui lòng liên hệ CSKH.",
    "invalid_amount": "Số tiền không hợp lệ. Vui lòng nhập một số dương.",

    # Withdrawal
    "withdrawal_ask_username": "Vui lòng nhập *TÊN TÀI KHOẢN GAME* của bạn để thực hiện rút tiền:",
    "withdrawal_ask_amount": "Vui lòng nhập *SỐ TIỀN* bạn muốn rút:",
    "withdrawal_processing": "Đang xử lý yêu cầu rút tiền của bạn. Vui lòng đợi trong giây lát...",
    "withdrawal_approved": "✅ Yêu cầu rút tiền {amount} của bạn đã được duyệt thành công!",
    "withdrawal_rejected_failed": "❌ Yêu cầu rút tiền của bạn bị từ chối: Rút tiền thất bại. Vui lòng liên hệ CSKH.",
    "withdrawal_rejected_wrong_info": "❌ Yêu cầu rút tiền của bạn bị từ chối: Sai thông tin ngân hàng hoặc tài khoản. Vui lòng kiểm tra lại.",
    "withdrawal_rejected_insufficient_balance": "❌ Yêu cầu rút tiền của bạn bị từ chối: Số dư không đủ.",
    "withdrawal_rejected_pending_deposit": "❌ Yêu cầu rút tiền của bạn bị từ chối: Có yêu cầu nạp tiền đang chờ xử lý.",
    "withdrawal_rejected_turnover": "❌ Yêu cầu rút tiền của bạn bị từ chối: Chưa đủ vòng cược. Vui lòng tiếp tục tham gia game.",
    "withdrawal_rejected_generic": "❌ Yêu cầu rút tiền của bạn bị từ chối: Lý do chung. Vui lòng liên hệ CSKH.",

    # Promotions general
    "promo_menu_intro": "Chào mừng bạn đến với mục Khuyến mãi. Chọn khuyến mãi bạn muốn yêu cầu:",
    "promo_kl001_intro": PROMO_TEXT_KL001,
    "promo_kl006_intro": PROMO_TEXT_KL006,
    "promo_kl007_intro": PROMO_TEXT_KL007.format(YESTERDAY_DMY=YESTERDAY_DMY),
    "promo_app_promo_intro": PROMO_TEXT_APP_PROMO,
    "ask_username_promo": "Vui lòng nhập *TÊN TÀI KHOẢN GAME* của bạn để yêu cầu khuyến mãi {promo_code}:",
    "ask_usernames_kl006": "Vui lòng nhập *TÊN TÀI KHOẢN GAME* của bạn và các thành viên khác trong nhóm (cách nhau bởi dấu phẩy) để yêu cầu KL006:",
    "ask_username_kl007": "Vui lòng nhập *TÊN TÀI KHOẢN GAME* của bạn để yêu cầu hoàn trả KL007.",
    "promo_request_sent": "✅ Yêu cầu khuyến mãi {promo_code} của bạn đã được gửi thành công!",
    "kl006_request_sent": "✅ Yêu cầu KL006 của nhóm bạn đã được gửi thành công!",
    "kl007_request_sent": "✅ Yêu cầu hoàn trả KL007 của bạn đã được gửi thành công!",
    "app_promo_request_sent": "✅ Yêu cầu khuyến mãi ứng dụng của bạn đã được gửi thành công!",

    # --- KHUYẾN MÃI TỔNG QUÁT VÀ TỪ CHỐI ---
    "promo_approved_message": "✅ Yêu cầu khuyến mãi {promo_code} của bạn đã được duyệt thành công!",
    "promo_rejected_wrong_id": "❌ Yêu cầu khuyến mãi {promo_code} bị từ chối: Sai ID người dùng hoặc tên game.",
    "promo_rejected_no_bank_link": "❌ Yêu cầu khuyến mãi {promo_code} bị từ chối: Bạn chưa liên kết ngân hàng. Vui lòng liên hệ CSKH.",
    "promo_rejected_already_claimed": "❌ Yêu cầu khuyến mãi {promo_code} bị từ chối: Bạn đã nhận khuyến mãi này rồi.",
    "promo_rejected_duplicate_ip": "❌ Yêu cầu khuyến mãi {promo_code} bị từ chối: Phát hiện trùng IP. Vui lòng liên hệ CSKH.",
    "promo_rejected_not_deposited": "❌ Yêu cầu khuyến mãi {promo_code} bị từ chối: Bạn chưa nạp tiền hoặc nạp không hợp lệ.",
    "promo_rejected_not_eligible": "❌ Yêu cầu khuyến mãi {promo_code} bị từ chối: Bạn không đủ điều kiện nhận khuyến mãi này.",
    "promo_rejected_multiple_deposits": "❌ Yêu cầu khuyến mãi {promo_code} bị từ chối: Bạn đã nạp nhiều hơn 1 lần.",
    "promo_rejected_already_wagered": "❌ Yêu cầu khuyến mãi {promo_code} bị từ chối: Bạn đã cược trước khi nhận khuyến mãi.",
    "promo_rejected_kl007_claimed_via_bot": "❌ Yêu cầu KL007 của bạn đã bị từ chối: Bạn đã nhận quà qua bot rồi.",
    "promo_rejected_kl007_not_eligible": "❌ Yêu cầu KL007 của bạn đã bị từ chối: Bạn chưa đủ điều kiện nhận quà.",
    "promo_rejected_kl007_not_reached_level": "❌ Yêu cầu KL007 của bạn đã bị từ chối: Bạn chưa đạt mức nhận quà.",
    "promo_rejected_generic": "❌ Yêu cầu khuyến mãi {promo_code} bị từ chối: Lý do khác. Vui lòng liên hệ CSKH.",

    # KL006 Specific responses
    "kl006_approved_message": "✅ Yêu cầu KL006 của nhóm bạn đã được duyệt thành công! (Nhóm {group_size} thành viên)",
    "kl006_rejected_no_group": "❌ Yêu cầu KL006 bị từ chối: Không tìm thấy nhóm của bạn. Vui lòng liên hệ CSKH.",
    "kl006_rejected_already_claimed": "❌ Yêu cầu KL006 bị từ chối: Nhóm của bạn đã nhận khuyến mãi này rồi.",
    "kl006_rejected_fake_members": "❌ Yêu cầu KL006 bị từ chối: Phát hiện thành viên ảo trong nhóm. Vui lòng liên hệ CSKH.",
    "kl006_rejected_other": "❌ Yêu cầu KL006 bị từ chối: Lý do khác. Vui lòng liên hệ CSKH.",

    # KL007 Point Response
    "kl007_point_response": "✅ Bạn đã nhận thành công {point} điểm hoàn trả từ KL007\\.",

    # App Promo Specific responses
    "app_promo_approved": "✅ Yêu cầu khuyến mãi Ứng dụng của bạn đã được duyệt thành công!",
    "app_promo_rejected_generic": "❌ Khuyến mãi Ứng dụng bị từ chối: Lý do khác. Vui lòng liên hệ CSKH.",
    "promo_rejected_app_promo_many_transactions": "❌ Khuyến mãi Ứng dụng bị từ chối: Bạn đã có nhiều giao dịch nạp/rút tiền.",
    "promo_rejected_app_promo_already_claimed": "❌ Khuyến mãi Ứng dụng bị từ chối: Bạn đã nhận khuyến mãi này rồi.",

    # Share Code
    "share_code_intro": "Bạn có {share_count} lượt chia sẻ\\\\. Mốc kế: {next_milestone}\\\\. Cần thêm: {needed_shares} lượt\\\\.",
    "share_code_intro_no_shares": "Hãy bắt đầu chia sẻ để nhận thưởng\\\\!",
    "all_milestones_achieved_text": "Đã hoàn thành tất cả",
    "check_reward_button_text": "Kiểm tra phần thưởng",
    "request_code_reward_button": "💰 Nhận Code thưởng",
    "get_my_share_link_button": "🔗 Link chia sẻ của tôi",
    "my_share_link_message": "Link của bạn: `{share_link}`",
    "error_getting_bot_info": "Lỗi: Không thể lấy thông tin bot\\\\. Vui lòng thử lại sau\\\\.",
    "error_no_referral_code": "Lỗi: Không tìm thấy mã giới thiệu\\\\. Thử lại /start\\\\.",
    "pending_claim_exists": "Yêu cầu trước đang xử lý cho mốc {milestone}\\\\.\\\\.\\\\.",
    "ask_username_for_share_reward": "Nhập username cho mốc {milestone}:",
    "no_new_milestone_message": "Cần {needed_more} lượt cho mốc {next_milestone}\\\\.",
    "all_milestones_claimed_message": "Bạn đã nhận tất cả phần thưởng chia sẻ có sẵn\\\\.",
    "share_reward_request_sent": "✅ Yêu cầu nhận thưởng mốc {milestone} của bạn đã được gửi thành công cho user: `{game_username}`\\\\.",
    "share_reward_approved": "✅ Yêu cầu nhận thưởng mốc {milestone} của bạn đã được duyệt thành công\\\\!",
    "share_reward_rejected_wrong_id": "❌ Yêu cầu nhận thưởng mốc {milestone} bị từ chối: Sai ID người dùng hoặc tên game\\\\.",
    "share_reward_contact_cskh": "ℹ️ Yêu cầu nhận thưởng mốc {milestone} của bạn cần được xem xét\\\\. Vui lòng liên hệ CSKH\\\\.",
    "share_reward_rejected_generic": "❌ Yêu cầu nhận thưởng mốc {milestone} bị từ chối: Lý do khác\\\\. Vui lòng liên hệ CSKH\\\\."
}