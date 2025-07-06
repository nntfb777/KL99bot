# texts.py

# ===================== PROMOTION DETAILS (used in handlers) =====================

PROMO_TEXT_KL001 = (
    "*Khuyến mãi KL001: Nạp đầu 199K tặng 199K*\n\n"
    "1\\. Áp dụng cho thành viên mới của *KL99* và chỉ nhận một lần duy nhất khi nạp lần đầu\\.\n"
    "2\\. Số tiền nạp tối thiểu là *199K*\\.\n"
    "3\\. Hoàn thành \\(tiền nạp \\+ tiền thưởng\\) x 1 vòng cược để rút tiền\\.\n"
    "4\\. Không áp dụng cho sảnh Xổ Số\\.\n"
    "5\\. Không áp dụng chung với các khuyến mãi nạp đầu khác\\.\n"
    "6\\. Áp dụng cho khách hàng chưa tham gia đặt cược\\.\n\n"
    "_Vui lòng xác nhận nếu bạn đồng ý với các điều kiện trên\\._"
)

PROMO_TEXT_KL006 = (
    "🎁 *Khuyến mãi đội nhóm KL006*\n\n"
    "*Điều kiện nhận thưởng:*\n"
    "1\\. Nhóm từ 3 hoặc 5 thành viên chơi game điện tử và bắn cá tại KL99\\.\n"
    "2\\. Mỗi thành viên cần có tổng cược hợp lệ tối thiểu 3,000 điểm trong ngày hôm qua\\.\n"
    "3\\. Tổng cược hợp lệ của cả nhóm cần đạt tối thiểu 20,000 điểm trong ngày hôm qua\\.\n"
    "4\\. Mỗi nhóm chỉ được nhận một lần mỗi ngày\\.\n\n"
    "_Vui lòng xác nhận nếu bạn đồng ý với các điều kiện trên\\._"
)

PROMO_TEXT_KL007 = (
    "🎁 *SIÊU TIỀN THƯỞNG \\- KL007*\n\n"
    "*Điều kiện nhận thưởng:*\n"
    "1\\. Thành viên có vé cược Nổ Hũ hoặc Bắn Cá thắng từ 500 điểm trở lên trong ngày hôm qua\\.\n"
    "2\\. Mỗi thành viên chỉ được nhận một lần mỗi ngày\\.\n"
    "3\\. Tiền thưởng sẽ được cộng trực tiếp vào tài khoản game\\.\n\n"
    "_Vui lòng xác nhận nếu bạn đồng ý với các điều kiện trên\\._"
)

PROMO_TEXT_APP_EXPERIENCE = (
    "🎁 *Khuyến mãi Trải nghiệm Tải App*\n\n"
    "*Điều kiện nhận thưởng:*\n"
    "1\\. Áp dụng cho thành viên tải ứng dụng KL99 lần đầu và đánh giá 5 sao\\.\n"
    "2\\. Mỗi tài khoản, mỗi thiết bị, mỗi IP chỉ được nhận một lần duy nhất\\.\n"
    "3\\. Cần cung cấp tên đăng nhập và hình ảnh xác nhận \\(nếu có\\)\\.\n"
    "4\\. KL99 có quyền thay đổi hoặc chấm dứt chương trình mà không cần báo trước\\.\n\n"
    "_Vui lòng xác nhận nếu bạn đồng ý với các điều kiện trên\\._"
)


# ===================== RESPONSE MESSAGES DICTIONARY =====================

RESPONSE_MESSAGES = {
    # --- Core & Common ---
    "welcome_message": "Chào mừng bạn đến với Bot hỗ trợ của KL99\\! Vui lòng chọn một tùy chọn bên dưới:",
    "request_cancelled": "Yêu cầu của bạn đã được hủy bỏ.",
    "yeu_cau_dang_xu_ly": "✅ Yêu cầu của bạn đã được gửi đi và đang chờ xử lý. Admin sẽ phản hồi trong thời gian sớm nhất.",
    "error_sending_request": "❌ Đã xảy ra lỗi khi xử lý yêu cầu. Vui lòng thử lại sau hoặc liên hệ CSKH.",
    "error_getting_bot_info": "Lỗi: Không thể lấy thông tin bot. Link chia sẻ có thể không hoạt động.",
    "choose_promo_message": "Vui lòng chọn một chương trình khuyến mãi:",

    # --- Buttons ---
    "back_to_menu_button": "⬅️ Quay lại Menu",
    "back_to_promo_menu_button_text": "⬅️ Menu Khuyến Mãi",
    "cskh_button_text": "💬 CSKH trực tuyến",
    "khuyen_mai_button_text": "🎁 Nhận khuyến mãi",
    "share_code_button_text": "🤝 Chia sẻ nhận Code",
    "download_app_button_text": "📱 Tải ứng dụng",
    "homepage_button_text": "🎮 Trang chủ",
    "facebook_button_text": "👍 Facebook",
    "telegram_channel_button_text": "📣 Kênh thông báo",
    "agree_button_text": "✅ Đồng ý",
    "promo_kl001_button": "🎉 Khuyến mãi KL001",
    "promo_kl006_button": "🔥 Khuyến mãi KL006",
    "promo_kl007_button": "✨ Khuyến mãi KL007",
    "promo_sharing_button": "🤝 Chia sẻ & nhận thưởng",
    "promo_app_button": "📲 Khuyến mãi Tải App",

    # --- Promo Ask Messages ---
    "ask_username_kl001": "Bạn đã đồng ý với điều khoản KL001\\. Vui lòng cung cấp *Tên đăng nhập* của bạn:",
    "ask_username_kl007": "Bạn đã đồng ý với điều khoản KL007\\. Vui lòng cung cấp *Tên đăng nhập* của bạn:",
    "ask_username_app_promo": "Bạn đã đồng ý với điều khoản KM Tải App\\. Vui lòng cung cấp *Tên đăng nhập* của bạn:",
    "kl006_agree_ask_group_size": "Bạn đã đồng ý với điều khoản KL006\\. Vui lòng chọn số lượng thành viên trong nhóm của bạn:",
    "kl006_ask_usernames": "Vui lòng cung cấp {group_size} tên đăng nhập của các thành viên \\( cách nhau bằng dấu phẩy hoặc dấu cách\\):",
    "kl006_invalid_username_count": "❌ Số lượng tên đăng nhập ({submitted_count}) không khớp với quy mô nhóm đã chọn ({expected_count} thành viên). Vui lòng nhập lại.",

    # --- Admin Responses (to User) ---
    "sai_id": "❌ Tên đăng nhập của bạn không chính xác. Vui lòng kiểm tra lại và đăng ký lại khuyến mãi.",
    "thanh_cong": "✅ Yêu cầu khuyến mãi của bạn đã được duyệt thành công! Vui lòng kiểm tra tài khoản game.",
    "CLKNH": "❌ Tài khoản của bạn chưa liên kết ngân hàng. Vui lòng liên kết trước khi đăng ký KM này.",
    "SaiTT": "❌ Thông tin tài khoản của bạn không hợp lệ. Vui lòng liên hệ CSKH để được hỗ trợ.",
    # KL001 Specific
    "kl001_welcome": "Chào mừng bạn đến với KM KL001! 🎁",
    "ask_username_kl001_after_agree": "Vui lòng nhập tên người dùng của bạn để hoàn tất 📋",
    "kl001_da_nhan": f"❌ Tài khoản của bạn đã nhận khuyến mãi KL001 trước đó.",
    "trung_ip": "❌ Tài khoản của bạn không đủ điều kiện nhận khuyến mãi do trùng IP.",
    "chua_nap": "❌ Khuyến mãi KL001 yêu cầu nạp tối thiểu 199K. Tài khoản của bạn chưa thực hiện giao dịch này.",
    "khong_du": "❌ Số tiền nạp đầu của bạn thấp hơn mức quy định. Vui lòng kiểm tra lại điều kiện.",
    #kl006
    # === THÊM DÒNG MỚI NÀY VÀO DICTIONARY ===
    "kl006_sai_id_user": "❌ Tên đăng nhập '{username}' trong danh sách nhóm của bạn không chính xác. Vui lòng kiểm tra lại.",
    "kl006_cuoc_khong_du_user": "❌ Thành viên '{username}' trong nhóm của bạn không đủ cược tối thiểu 3,000 điểm (Bắn Cá/Nổ Hũ) trong ngày {yesterday_date}.",
    "kl006_khong_du_tong_diem": "❌ Tổng cược hợp lệ của nhóm bạn trong ngày {yesterday_date} không đủ 20,000 điểm.",
    "kl006_da_nhan": "❌ Nhóm của bạn đã nhận KM KL006 trong ngày {yesterday_date}.",
    "kl006_nhom_chua_dk": "❌ Nhóm của  bạn chưa đăng kí nên không đủ điều kiện nhận khuyến mãi này. Hãy vui lòng  liên hệ CSKH để đăng ký nhóm.",
    "kl006_thanh_cong": "✅ Yêu cầu khuyến mãi KL006 của bạn đã được duyệt thành công! Vui lòng kiểm tra tài khoản game của các thành viên.",
    # KL007 Specific
    "kl007_wait_message": "🎁 Khuyến mãi KL007 sẽ bắt đầu được nhận thưởng cho ngày hôm nay sau 12:00 trưa\\. Vui lòng quay lại sau nhé\\!",
    "kl007_points_added": "Bạn đã được cộng {points} điểm KL007 ✨",
    "khong_co_ve_kl007": "❌ Tài khoản của bạn không có vé cược thắng Nổ Hũ/Bắn Cá từ 500 điểm trở lên vào ngày {yesterday_date}.",
    "kl007_da_nhan": "❌ Tài khoản của bạn đã nhận khuyến mãi KL007 trong ngày hôm nay.",
    "thanh_cong_kl007_points": "✅ Yêu cầu KM KL007 của bạn đã được duyệt. *{points}* điểm đã được cộng vào tài khoản `{customer_username}`.",
    # App Promo Specific
    "app_promo_dn": "❌ Tài khoản của bạn đã nhận khuyến mãi Tải App trước đó.",
    "app_promo_ha": "🖼️ Admin yêu cầu bạn cung cấp hình ảnh xác nhận tải app và đánh giá 5 sao. Vui lòng đăng ký lại và gửi kèm hình ảnh.",
    "app_promo_ip": "❌ Tài khoản của bạn không đủ điều kiện nhận KM Tải App do trùng IP.",
    "app_promo_ask_image": "Bạn có hình ảnh xác nhận đã nhận được quảng cáo của chúng tôi không?",
    "app_promo_request_image": "Tuyệt vời! Vui lòng gửi hình ảnh đó vào đây.",
    "app_promo_no_image_sent_to_admin": "✅ Yêu cầu KM Tải App \\(không có ảnh\\) của bạn đã được gửi đi\\.",

    # --- Sharing Feature ---
    "share_code_intro": "🎁 *CHIA SẺ NHẬN CODE TRI ÂN*\n\nSố lượt chia sẻ của bạn: *{share_count}*\\.\nMốc thưởng tiếp theo: *{next_milestone}* \\(cần thêm *{needed_shares}* lượt\\)\\.",
    "share_code_intro_no_shares": "🎁 *CHIA SẺ NHẬN CODE TRI ÂN*\n\nBạn chưa có lượt chia sẻ nào\\. Hãy bắt đầu chia sẻ để nhận thưởng tại mốc *15* lượt\\!",
    "all_milestones_claimed_message": "🎉 Chúc mừng\\! Bạn đã nhận thưởng cho tất cả các mốc chia sẻ hiện có\\. Cảm ơn sự đóng góp của bạn\\.",
    "get_my_share_link_button": "🔗 Link chia sẻ của tôi",
    "request_code_reward_button": "💰 Nhận thưởng",
    "my_share_link_message": "Đây là link chia sẻ của bạn:\n`{share_link}`\nGửi link này cho bạn bè để mời họ tham gia nhé\\.",
    "no_new_milestone_message": "Bạn có {share_count} lượt chia sẻ\\. Cần thêm {needed_more} lượt nữa để đạt mốc {next_milestone}\\. Cố gắng lên nhé\\!",
    "ask_username_for_share_reward": "🎉 Chúc mừng\\! Bạn đã đạt mốc {milestone} lượt chia sẻ\\. Vui lòng cung cấp Tên đăng nhập game của bạn để nhận thưởng:",
    "share_reward_request_sent": "✅ Yêu cầu nhận thưởng cho mốc *{milestone}* với tên đăng nhập *{game_username}* đã được gửi đi\\.",
    "share_reward_approved": "✅ Chúc mừng\\! Yêu cầu nhận thưởng mốc *{milestone}* của bạn đã được duyệt\\. Phần thưởng sẽ sớm được cộng vào tài khoả\\.",
    "share_reward_sai_id": "❌ Tên đăng nhập bạn cung cấp cho mốc thưởng *{milestone}* không chính xác\\. Vui lòng liên hệ CSKH\\.",
    "share_reward_cskh": "ℹ️ Có vấn đề với yêu cầu nhận thưởng mốc *{milestone}* của bạn\\. Vui lòng liên hệ CSKH để được hỗ trợ\\.",

        # --- Transaction Flow (deposit/Rút) ---
    "transaction_menu_button": "💸 Hỗ trợ Nạp/Rút",
    "transaction_menu_intro": "Vui lòng chọn vấn đề bạn cần hỗ trợ:",
    "transaction_deposit_button": "📥 Nạp tiền",
    "transaction_withdraw_button": "📤 Rút tiền",

    # Luồng Nạp tiền
    "ask_username_deposit": "Vui lòng cung cấp *Tên đăng nhập game* của bạn để kiểm tra giao dịch NẠP TIỀN:",
    "ask_for_receipt": "Cảm ơn bạn. Vui lòng gửi HÌNH ẢNH hóa đơn/biên lai chuyển khoản của bạn vào đây. Hóa đơn cần hiển thị rõ số tiền và thông tin người nhận.",
    "receipt_received_thanks": "✅ Đã nhận được hóa đơn của bạn. Yêu cầu đang được gửi đến admin...",
    "deposit_thanh_cong": "✅ Yêu cầu hỗ trợ nạp tiền của bạn đã được xử lý thành công\\.",
    "deposit_sai_id": "❌ Yêu cầu hỗ trợ nạp tiền của bạn đã bị từ chối\\. Lý do: Tên đăng nhập không chính xác\\.",
    "deposit_da_len_trang_khac": "ℹ️ Giao dịch của bạn dường như đã được xử lý ở một nền tảng khác\\. Vui lòng kiểm tra lại hoặc liên hệ CSKH\\.",
    "deposit_khong_phai_cua_chung_toi": "❌ Giao dịch này không phải của chúng tôi\\. Vui lòng kiểm tra lại thông tin người nhận\\.",
    "deposit_hoa_don_khong_dung": "❌ Hóa đơn bạn cung cấp không hợp lệ hoặc không rõ ràng\\. Vui lòng cung cấp hóa đơn chính xác và tạo lại yêu cầu\\.",
    "deposit_chua_nhan_duoc_tien": "ℹ️ Chúng tôi chưa nhận được khoản tiền từ giao dịch của bạn\\. Vui lòng đợi thêm hoặc liên hệ ngân hàng của bạn\\.",
    "deposit_lam_lai_lenh": "ℹ️ Admin yêu cầu bạn tạo lại lệnh nạp tiền với cổng thanh toán *{payment_gateway}* và thực hiện lại giao dịch\\.",
    "deposit_da_len_diem": "✅ Giao dịch của bạn đã được xác nhận và lên điểm vào lúc *{process_time}*\\. Vui lòng kiểm tra lại tài khoản game\\.",

    # Luồng Rút tiền
    "ask_username_withdraw": "Vui lòng cung cấp *Tên đăng nhập game* của bạn để kiểm tra giao dịch RÚT TIỀN:",
    "ask_for_amount": "Cảm ơn bạn. Vui lòng nhập SỐ TIỀN bạn đã rút (chỉ nhập số, ví dụ: 500000):",
    "invalid_amount": "❌ Số tiền không hợp lệ. Vui lòng chỉ nhập số.",
    "amount_received_thanks": "✅ Đã nhận được thông tin. Yêu cầu đang được gửi đến admin...",
    "withdraw_thanh_cong": "✅ Yêu cầu hỗ trợ rút tiền của bạn đã được xử lý thành công.",
    "withdraw_gui_hd": "ℹ️ Giao dịch của bạn đã được thực hiện. Admin sẽ sớm gửi hóa đơn/biên lai cho bạn. Vui lòng đợi.",
    "withdraw_sai_tt": "❌ Yêu cầu hỗ trợ rút tiền của bạn đã bị từ chối do thông tin tài khoản nhận không chính xác. Vui lòng kiểm tra và thử lại.",
    "withdraw_yeu_cau_sao_ke": "ℹ️ Để xác minh giao dịch, admin yêu cầu bạn cung cấp sao kê ngân hàng cho khoảng thời gian thực hiện lệnh rút. Vui lòng liên hệ CSKH để cung cấp.",
    "withdraw_bao_tri": "ℹ️ Hệ thống rút tiền đang trong thời gian bảo trì. Giao dịch của bạn sẽ được xử lý ngay khi hệ thống hoạt động trở lại. Xin cảm ơn!",
    "withdraw_cskh": "ℹ️ Có vấn đề với yêu cầu hỗ trợ rút tiền của bạn. Vui lòng liên hệ CSKH để được hỗ trợ.",


    # --- Referral ---
    "referral_successful_notification_to_referrer": "🎉 Chúc mừng\\! Bạn vừa có thêm 1 lượt chia sẻ thành công\\. Tổng lượt chia sẻ hiện tại: *{share_count}*\\.",
    "new_user_welcome_referred": "Chào mừng bạn đến với KL99\\! Bạn được giới thiệu bởi *{referrer_name}*\\.",
    "cannot_refer_self": "Bạn không thể tự giới thiệu chính mình\\.",
}