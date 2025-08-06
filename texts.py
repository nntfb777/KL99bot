# texts.py

# ===================== PROMOTION DETAILS (used in handlers) =====================

PROMO_TEXT_KL001 = (
    "*Khuyến mãi KL001: Nạp đầu 199K tặng 199K*\n\n"
    "1\\. Áp dụng cho thành viên mới của *KL99* và chỉ nhận một lần duy nhất khi nạp lần đầu\\.\n"
    "2\\. Số tiền nạp tối thiểu là *199K*\\.\n"
    "3\\. Hoàn thành \\(tiền nạp \\+ tiền thưởng\\) x 1 vòng cược để rút tiền\\.\n"
    "4\\. Chỉ áp dụng cho trò chơi *Nổ Hũ* và *Bắn Cá*\\.\n"
    "5\\. Không áp dụng chung với các khuyến mãi nạp đầu khác\\.\n"
    "6\\. Áp dụng cho khách hàng chưa tham gia đặt cược\\.\n\n"
    "_Vui lòng xác nhận nếu quý khách đồng ý với các điều kiện trên\\._"
)

PROMO_TEXT_KL006 = (
    "🎁 *Khuyến mãi đội nhóm KL006*\n\n"
    "*Điều kiện nhận thưởng:*\n"
    "1\\. Nhóm từ 3 hoặc 5 thành viên chơi game Nổ Hũ và Bắn Cá tại KL99\\.\n"
    "2\\. Mỗi thành viên cần có tổng cược hợp lệ tối thiểu 3,000 điểm trong ngày hôm qua\\.\n"
    "3\\. Tổng cược hợp lệ của cả nhóm cần đạt tối thiểu 20,000 điểm trong ngày hôm qua\\.\n"
    "4\\. Đã đăng ký nhóm ít nhất 24 giờ\\.\n\n"
    "_Vui lòng xác nhận nếu quý khách đồng ý với các điều kiện trên\\._"
)

PROMO_TEXT_KL007 = (
    "🎁 *SIÊU TIỀN THƯỞNG \\- KL007*\n\n"
    "*Điều kiện nhận thưởng:*\n"
    "1\\. Thành viên có vé cược Nổ Hũ hoặc Bắn Cá thắng từ 500 điểm trở lên tại trò chơi *Nổ Hũ* và *Bắn Cá* trong ngày hôm qua\\.\n"
    "2\\. Mỗi thành viên chỉ được nhận một lần cho vé cược cao nhất mỗi ngày\\.\n"
    "3\\. Tiền thưởng sẽ được cộng trực tiếp vào tài khoản game\\.\n\n"
    "_Vui lòng xác nhận nếu quý khách đồng ý với các điều kiện trên\\._"
)

PROMO_TEXT_APP_EXPERIENCE = (
    "🎁 *Khuyến mãi Trải nghiệm Tải App*\n\n"
    "*Điều kiện nhận thưởng:*\n"
    "1\\. Áp dụng cho thành viên tải ứng dụng KL99 lần đầu\\.\n"
    "2\\. Mỗi tài khoản, mỗi thiết bị, mỗi IP chỉ được nhận một lần duy nhất\\.\n"
    "3\\. Cần cung cấp tên đăng nhập và hình ảnh xác nhận \\(nếu có\\)\\.\n"
    "4\\. KL99 có quyền thay đổi hoặc chấm dứt chương trình mà không cần báo trước\\.\n\n"
    "_Vui lòng xác nhận nếu quý khách đồng ý với các điều kiện trên\\._"
)


# ===================== RESPONSE MESSAGES DICTIONARY =====================

RESPONSE_MESSAGES = {
    # --- Core & Common ---
    "welcome_message": "Chào mừng quý khách đến với Bot hỗ trợ của `KL99` \\! Vui lòng chọn một tùy chọn bên dưới:",
    "yeu_cau_dang_xu_ly": "✅ Yêu cầu của quý khách đang được xử lý\\. Hệ thống `KL99` sẽ phản hồi trong thời gian sớm nhất\\.",
    "error_sending_request": "❌ Đã xảy ra lỗi khi xử lý yêu cầu\\. Vui lòng thử lại sau hoặc liên hệ CSKH\\.",
    "error_getting_bot_info": "Lỗi: Không thể lấy thông tin bot\\. Link chia sẻ có thể không hoạt động\\.",
    "choose_promo_message": "Vui lòng chọn một chương trình khuyến mãi mà quý khách muốn nhận thưởng:",


    # --- Buttons ---
    "register_button_text": "📝 Đăng ký",
    "back_to_menu_button": "⬅️ Quay lại Menu",
    "back_to_promo_menu_button_text": "⬅️ Menu Khuyến Mãi",
    "cskh_button_text": "💬 CSKH trực tuyến",
    "khuyen_mai_button_text": "🎁 Nhận khuyến mãi",
    "share_code_button_text": "🤝 Chia sẻ nhận Code",
    "download_app_button_text": "📱 Tải ứng dụng",
    "homepage_button_text": "🎮 Link mới nhất",
    "facebook_button_text": "👍 Facebook",
    "telegram_channel_button_text": "📣 Kênh thông báo",
    "agree_button_text": "✅ Đồng ý",
    "promo_kl001_button": "🎉 Khuyến Mãi Nạp Đầu KL001",
    "promo_kl006_button": "🔥 Thưởng Đội Nhóm KL006",
    "promo_kl007_button": "✨ Vé Cược Thắng Lớn KL007",
    "promo_sharing_button": "🤝 Chia sẻ & nhận thưởng",
    "promo_app_button": "📲 Khuyến mãi Tải App",

    "provide_game_link_header": "✅ Đã cập nhật link truy cập mới nhất cho quý khách \\!",
    "provide_game_link_body": "🔗 **Link mới nhất :**",
    "provide_game_link_instruction": "Vui lòng sao chép link và dán vào trình duyệt nếu quý khách không thể mở trực tiếp\\.\n Nếu quý khách vẫn không thể truy cập được, hãy chụp ảnh màn hình và báo cáo lại cho chúng tôi để có trải nghiệm tốt nhất\\!\n Cảm ơn sự hợp tác của quý khách \\!",
    "refresh_link_button_text": "🔄 Đổi link mới",
    "report_link_button_text": "⚠️ Báo cáo lỗi",
    "report_link_success_alert": "Cảm ơn quý khách đã báo cáo! Đang lấy link mới cho quý khách ...",
    "ask_for_error_image": "Để hệ thống `KL99` hỗ trợ tốt hơn, quý khách có hình ảnh chụp màn hình lỗi không\\?",
    "yes_button": "✅ Có, tôi có ảnh",
    "no_button": "❌ Không, chỉ gửi báo cáo",
    "please_send_image": "Vui lòng gửi hình ảnh đó vào đây\\.",
    "report_sent_with_image": "✅ Đã gửi báo cáo kèm hình ảnh của quý khách \\.",
    "report_sent_without_image": "✅ Đã gửi báo cáo của quý khách \\.",
    "invalid_message_in_report_flow": "Vui lòng sử dụng các nút bấm hoặc gửi hình ảnh theo yêu cầu\\.",
    "ask_about_vpn": "Để giúp chúng tôi kiểm tra tốt hơn, quý khách có đang sử dụng ứng dụng 1.1.1.1 (hoặc VPN) không?",
    "ask_about_vpnn": "Để giúp chúng tôi kiểm tra tốt hơn, quý khách có đang sử dụng ứng dụng 1\\.1\\.1\\.1 \\(hoặc VPN\\) không\\?",

    # --- Promo Ask Messages ---
    "out_of_requests": "� Quý khách đã hết lượt khuyến mãi hôm nay, vui lòng lòng liên  hệ CSKH trực tuyến.",
    "ask_username_kl001": "Quý khách đã đồng ý với điều khoản KL001\\. Vui lòng cung cấp *Tên đăng nhập* của quý khách :",
    "ask_username_kl007": "Quý khách đã đồng ý với điều khoản KL007\\. Vui lòng cung cấp *Tên đăng nhập* của quý khách :",
    "ask_username_app_promo": "Quý khách đã đồng ý với điều khoản KM Tải App\\. Vui lòng cung cấp *Tên đăng nhập* của quý khách :",
    "kl006_agree_ask_group_size": "Quý khách đã đồng ý với điều khoản KL006\\. Vui lòng chọn số lượng thành viên trong nhóm của quý khách:",
    "kl006_ask_usernames": "Vui lòng cung cấp {group_size} tên đăng nhập của các thành viên `\\( cách nhau bằng dấu phẩy hoặc dấu cách\\)`:",
    "kl006_invalid_username_count": "❌ Số lượng tên đăng nhập {submitted_count} không khớp với quy mô nhóm đã chọn {expected_count} thành viên\\. Vui lòng nhập lại\\.",

    # --- Admin Responses (to User) ---
    "sai_id": "❌ Tên đăng nhập của quý khách không chính xác\\. Vui lòng kiểm tra lại và đăng ký lại khuyến mãi\\.",
    "thanh_cong": "✅ Yêu cầu khuyến mãi của quý khách đã được duyệt thành công\\! Vui lòng kiểm tra tài khoản game\\.",
    "CLKNH": "❌ Tài khoản của quý khách chưa liên kết ngân hàng\\. Vui lòng liên kết trước khi đăng ký khuyến mãi này\\.",
    "SaiTT": "❌ Thông tin tài khoản của quý khách không chính xác\\. Vui lòng liên hệ CSKH để được hỗ trợ\\.",
    # KL001 Specific
    "ask_username_kl001_after_agree": "Vui lòng nhập tên người dùng của quý khách 📋",
    "kl001_da_nhan": f"❌ Tài khoản của quý khách đã nhận khuyến mãi KL001 trước đó\\. Vui lòng kiểm tra lại\\.",
    "trung_ip": "❌ Tài khoản của quý khách không đủ điều kiện nhận khuyến mãi do trùng IP\\.",
    "chua_nap": "❌ Khuyến mãi KL001 yêu cầu nạp tối thiểu 199K\\. Tài khoản của quý khách chưa thực hiện giao dịch này nên không đủ điều kiện nhận khuyến mãi KL001\\.",
    "khong_du": "❌ Số tiền nạp đầu của quý khách thấp hơn mức tối thiểu là 199 nên không đủ điều kiện nhận khuyến mãi này\\. Vui lòng kiểm tra lại điều kiện\\.",
    "da_cuoc": "❌ Yêu cầu của quý khách không được duyệt vì tài khoản đã có phát sinh cược trước khi đăng ký khuyến mãi\\. Vui lòng liên hệ CSKH để biết thêm chi tiết\\.",
    #kl006
    # === THÊM DÒNG MỚI NÀY VÀO DICTIONARY ===
    "kl006_wait_message": "🎁 Khuyến mãi KL006 sẽ bắt đầu được nhận thưởng cho ngày hôm nay sau 12:00 trưa\\. Vui lòng quay lại sau nhé\\!",
    "kl006_sai_id_user": "❌ Tên đăng nhập '{username}' trong danh sách nhóm của quý khách không chính xác\\. Vui lòng kiểm tra lại\\.",
    "kl006_cuoc_khong_du_user": "❌ Thành viên '{username}' trong nhóm của quý khách không đủ cược tối thiểu 3,000 điểm (Bắn Cá/Nổ Hũ) trong ngày {yesterday_date}\\.",
    "kl006_khong_du_tong_diem": "❌ Tổng cược hợp lệ của nhóm quý khách trong ngày {yesterday_date} không đủ 20,000 điểm\\.",
    "kl006_da_nhan": "❌ Nhóm của quý khách đã nhận KM KL006 trong ngày {yesterday_date}\\.",
    "kl006_nhom_chua_dk": "❌ Nhóm của  quý khách chưa đăng kí nên không đủ điều kiện nhận khuyến mãi này\\. Hãy vui lòng  liên hệ CSKH để đăng ký nhóm\\.",
    "kl006_thanh_cong": "✅ Yêu cầu khuyến mãi KL006 của quý khách đã được duyệt thành công\\! Vui lòng kiểm tra tài khoản game của các thành viên\\.",
    "kl006_group_not_registered": "❌ Không tìm thấy nhóm của quý khách trong danh sách đăng ký cho ngày `{yesterday_date}`\\. Vui lòng liên hệ CSKH để đăng ký\\.",
    "kl006_members_mismatch": "❌ Thành viên `{mismatched_members}` không thuộc nhóm đã đăng ký cho ngày `{yesterday_date}`\\. Vui lòng kiểm tra lại\\.",
    "kl006_low_bet_members": (
        "❌ Nhóm của quý khách có thành viên không đủ 3,000 điểm cược cho ngày `{yesterday_date}`:\n\n"
        "{bets_details_list}"
    ),
    # Hiển thị cả tổng cược của nhóm
    "kl006_group_ineligible": (
        "❌ Tổng cược của nhóm quý khách trong ngày `{yesterday_date}` không đủ điều kiện nhận thưởng\\.\n\n"
        "**Chi tiết cược:**\n"
        "{bets_details_list}\n" #
        "**Tổng cược nhóm:** `{group_total_bet:,.0f}` điểm\\."
    ),
    "kl006_already_claimed": "✅ Nhóm của quý khách đã nhận thưởng cho ngày `{yesterday_date}`  , vui lòng kiểm tra lại\\.",
    # KL007 Specific
    "kl007_wait_message": "🎁 Khuyến mãi KL007 sẽ bắt đầu được nhận thưởng cho ngày hôm nay sau 12:00 trưa\\. Vui lòng quay lại sau nhé\\!",
    "kl007_points_added": "Quý khách đã được cộng {points} điểm từ khuyến mãi KL007 ✨\\. Vui lòng đăng nhập và kiểm tra\\. Chúc quý khách may mắn\\!",
    "khong_co_ve_kl007": "❌ Tài khoản của quý khách không có vé cược thắng Nổ Hũ/Bắn Cá từ 500 điểm trở lên vào ngày {yesterday_date}, nếu quý khách có vé vui lòng liên hệ CSKH trực tuyến và cung cấp hình ảnh vé cược\\.",
    "kl007_da_nhan": "❌ Tài khoản của quý khách đã nhận khuyến mãi KL007  của ngày `{yesterday_date}`, vui lòng kiểm tra lại tại lịch sử giao dịch\\.",
    # App Promo Specific
    "app_promo_dn": "❌ Tài khoản của quý khách đã nhận khuyến mãi Tải App trước đó\\.",
    "app_promo_ha": "🖼️ Admin yêu cầu quý khách cung cấp hình ảnh xác nhận tải app\\. Vui lòng đăng ký lại và gửi kèm hình ảnh\\.",
    "app_promo_ip": "❌ Tài khoản của quý khách không đủ điều kiện nhận KM Tải App do trùng IP.",
    "app_promo_ask_image": "quý khách có hình ảnh xác nhận đã nhận được quảng cáo của chúng tôi không?",
    "app_promo_request_image": "Tuyệt vời! Vui lòng gửi hình ảnh đó vào đây.",
    "app_promo_request_image_again": "Định dạng hình ảnh của quý khách không chính xác, vui lòng kiểm tra lại và gửi chính xác",
    "app_promo_no_image_sent_to_admin": "✅ Yêu cầu KM Tải App \\(không có ảnh\\) của quý khách đã được gửi đi\\.",


    # --- Sharing Feature ---
    "share_code_intro": "🎁 *CHIA SẺ NHẬN CODE TRI ÂN*\n\nSố lượt chia sẻ của quý khách: *{share_count}*\\.\nMốc thưởng tiếp theo: *{next_milestone}* \\(cần thêm *{needed_shares}* lượt\\)\\.",
    "share_code_intro_no_shares": "🎁 *CHIA SẺ NHẬN CODE TRI ÂN*\n\n Quý khách chưa có lượt chia sẻ nào\\. Hãy bắt đầu chia sẻ để nhận thưởng tại mốc *15* lượt\\!",
    "all_milestones_claimed_message": "🎉 Chúc mừng\\! quý khách đã nhận thưởng cho tất cả các mốc chia sẻ hiện có\\. Cảm ơn sự đóng góp của quý khách \\.",
    "get_my_share_link_button": "🔗 Link chia sẻ của tôi",
    "request_code_reward_button": "💰 Nhận thưởng",
    "my_share_link_message": "Đây là link chia sẻ của quý khách:\n{share_link}\nGửi link này cho quý khách để mời họ tham gia nhé\\.",
    "no_new_milestone_message": "Quý khách có {share_count} lượt chia sẻ\\. Cần thêm {needed_more} lượt nữa để đạt mốc {next_milestone}\\. Cố gắng lên nhé\\!",
    "ask_username_for_share_reward": "🎉 Chúc mừng\\! Quý khách đã đạt mốc {milestone} lượt chia sẻ\\. Vui lòng cung cấp Tên đăng nhập game của quý khách để nhận thưởng:",
    "share_reward_request_sent": "✅ Yêu cầu nhận thưởng cho mốc *{milestone}* với tên đăng nhập *{game_username}* đã được gửi đi\\.",
    "share_reward_approved": "✅ Chúc mừng\\! Yêu cầu nhận thưởng chia sẻ của quý khách đã được cập nhật thành công\\. Phần thưởng {reward_points} điểm đã được cộng vào tài khoản của quý khách\\.",
    "share_reward_sai_id": "❌ Yêu cầu nhận thưởng cho mốc {milestone} với ID Game `{game_username}` của quý khách đã bị từ chối do sai thông tin\\. Vui lòng liên hệ CSKH\\.",
    "share_reward_cskh": "ℹ️ Yêu cầu nhận thưởng cho mốc {milestone} của quý khách cần được xác minh thêm\\. Vui lòng liên hệ CSKH trực tuyến để được hỗ trợ\\.",
    "admin_resp_lam_dung": (
        "⚠️ *Thông báo từ hệ thống KL99* ⚠️\n\n"
        "Chúng tôi đã phát hiện hoạt động bất thường từ tài khoản của quý khách\\.\n"
        "Yêu cầu khuyến mãi hiện tại của quý khách đã bị từ chối\\.\n\n"
        "Vui lòng tuân thủ đúng các điều khoản và điều kiện để tránh bị hạn chế trong tương lai\\."
    ),
    "share_reward_can_lknh": "❌ Yêu cầu nhận thưởng cho mốc {milestone} của quý khách chưa thể xử lý do tài khoản chưa liên kết ngân hàng\\. Vui lòng hoàn tất liên kết và thử lại\\.",

        # --- Transaction Flow (deposit/Rút) ---
    "transaction_menu_button": "💸 Hỗ trợ Nạp/Rút",
    "transaction_menu_intro": "Vui lòng chọn vấn đề quý khách cần hỗ trợ:",
    "transaction_deposit_button": "📥 Nạp tiền",
    "transaction_withdraw_button": "📤 Rút tiền",
    "out_of_requests_trans": "quý khách đã hết lượt yêu cầu nạp và rút tiền hôm nay.",

    # Luồng Nạp tiền
    "ask_username_deposit": "Vui lòng cung cấp *Tên đăng nhập game* của quý khách để kiểm tra giao dịch NẠP TIỀN:",
    "ask_for_receipt": "Cảm ơn quý khách. Vui lòng gửi HÌNH ẢNH hóa đơn/biên lai chuyển khoản của quý khách vào đây. Hóa đơn cần hiển thị rõ số tiền và thông tin người nhận.",
    "receipt_received_thanks": "✅ Đã nhận được hóa đơn của quý khách. Yêu cầu đang được xử lý... KL99 sẽ thông báo ngay khi kiểm tra hoàn tất\\.",
    "deposit_thanh_cong": "✅ Yêu cầu hỗ trợ nạp tiền của quý khách đã được xử lý thành công\\. Vui lòng đăng nhập và kiểm tra lại số dư\\.",
    "deposit_sai_id": "❌ Yêu cầu hỗ trợ nạp tiền của quý khách đã bị từ chối\\. Lý do: Tên đăng nhập không chính xác\\.",
    "deposit_da_len_trang_khac": "ℹ️ Giao dịch của quý khách đã được xử lý ở một nền tảng khác\\. Vui lòng kiểm tra lại hoặc liên hệ CSKH\\.",
    "deposit_khong_phai_cua_chung_toi": "❌ Giao dịch này không phải của chúng tôi\\. Vui lòng kiểm tra lại thông tin người nhận\\.",
    "deposit_hoa_don_khong_dung": "❌ Hóa đơn quý khách cung cấp không hợp lệ hoặc không rõ ràng\\. Vui lòng cung cấp hóa đơn chính xác và tạo lại yêu cầu\\.",
    "deposit_chua_nhan_duoc_tien": "ℹ️ Hệ thống chưa nhận được khoản tiền từ giao dịch của quý khách\\. Vui lòng đợi thêm, khi nào nhận được tiền của quý khách, hệ thống sẽ cập nhật điểm\\.",
    "deposit_lam_lai_lenh": "ℹ️ Vui lòng tạo lại lệnh nạp tiền với cổng thanh toán *{payment_gateway}* và không thực hiện giao dịch chuyển tiền\\.",
    "deposit_da_len_diem": "✅ Giao dịch của quý khách đã được xác nhận và lên điểm vào lúc *{process_time}*\\. Vui lòng kiểm tra lại tài khoản game\\.",

    # Luồng Rút tiền
    "ask_username_withdraw": "Vui lòng cung cấp *Tên đăng nhập game* của quý khách để kiểm tra giao dịch RÚT TIỀN:",
    "ask_for_amount": "Cảm ơn quý khách \\. Vui lòng nhập SỐ TIỀN quý khách đã rút \\(chỉ nhập số, ví dụ: 5000\\):",
    "invalid_amount": "❌ Số tiền không hợp lệ\\. Vui lòng chỉ nhập số\\.",
    "amount_received_thanks": "✅ Đã nhận được thông tin\\. Yêu cầu đang được xử lý\\.\\.\\. KL99 sẽ thông báo ngay khi kiểm tra hoàn tất",
    "withdraw_thanh_cong": "✅ Yêu cầu hỗ trợ rút tiền của quý khách đã được xử lý thành công\\.",
    "withdraw_gui_hd": "ℹ️ Giao dịch của quý khách đã được thực hiện\\. Admin sẽ sớm gửi hóa đơn/biên lai cho quý khách \\. Vui lòng đợi\\.",
    "withdraw_sai_tt": "❌ Yêu cầu hỗ trợ rút tiền của quý khách đã bị từ chối do thông tin tài khoản nhận không chính xác\\. Vui lòng liên hệ CSKH trực tuyến để được hỗ trợ \\.",
    "withdraw_yeu_cau_sao_ke": "ℹ️ Để xác minh giao dịch,quý khách vui lòng cung cấp sao kê ngân hàng từ khoảng thời gian thực hiện lệnh rút\\. Vui lòng liên hệ CSKH để cung cấp\\.",
    "withdraw_bao_tri": "ℹ️ Hệ thống rút tiền đang trong thời gian bảo trì\\. Giao dịch của quý khách sẽ được xử lý ngay khi hệ thống hoạt động trở lại\\. Xin cảm ơn\\!",
    "withdraw_cskh": "ℹ️ Có vấn đề với yêu cầu hỗ trợ rút tiền của quý khách\\. Vui lòng liên hệ CSKH để được hỗ trợ\\.",
    "withdraw_ko_co_lenh": "❌ Hệ thống không tìm thấy lệnh rút mà quý khách yêu cầu\\. Vui lòng kiểm tra lại\\.",

    "cskh_vpn_warning_text": "⚠️ *Lưu ý quan trọng* ⚠️\n\nNếu quý khách đang sử dụng ứng dụng `1\\.1\\.1\\.1` hoặc các phần mềm `VPN` khác, vui lòng *tắt các ứng dụng này* trước khi liên hệ CSKH để đảm bảo kết nối được ổn định và không bị gián đoạn\\.",
    "invalid_username_format": "❌ *Tên đăng nhập* không chính xác, xin vui lòng kiểm tra lại \\.",
    # --- Referral ---
    "sharing_share_text_template": "🎁 Đăng ký tài khoản qua link của tôi và nhận ngay phần thưởng hấp dẫn! \n{share_link}",
    "back_to_sharing_menu_button": "⬅️ Quay lại Menu",
    "referral_successful_notification_to_referrer": "🎉 Chúc mừng\\! quý khách vừa có thêm 1 lượt chia sẻ thành công\\. \nTổng lượt chia sẻ hiện tại: *{share_count}*\\.",
    "new_user_welcome_referred": "Chào mừng quý khách đến với KL99\\! quý khách được giới thiệu bởi *{referrer_name}*\\.",
    "cannot_refer_self": "Quý khách không thể tự giới thiệu chính mình\\.",
}