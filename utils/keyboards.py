# utils/keyboards.py
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from texts import RESPONSE_MESSAGES
import config

# --- General Purpose Keyboards ---

def create_main_menu_markup() -> InlineKeyboardMarkup:
    """Creates the main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES["khuyen_mai_button_text"], callback_data='show_promo_menu')],
        [InlineKeyboardButton(RESPONSE_MESSAGES["share_code_button_text"], callback_data='share_code_entry_point')],
        [InlineKeyboardButton(RESPONSE_MESSAGES["transaction_menu_button"], callback_data='transaction_entry_point')],
        [
            InlineKeyboardButton(RESPONSE_MESSAGES["download_app_button_text"], url=config.APP_DOWNLOAD_LINK),
            InlineKeyboardButton(RESPONSE_MESSAGES["homepage_button_text"], url=random.choice(config.GAME_LINKS))
        ],
        [
            InlineKeyboardButton(RESPONSE_MESSAGES["facebook_button_text"], url=config.FACEBOOK_LINK),
            InlineKeyboardButton(RESPONSE_MESSAGES["telegram_channel_button_text"], url=config.TELEGRAM_CHANNEL_LINK)
        ],
        [InlineKeyboardButton(RESPONSE_MESSAGES["cskh_button_text"], url=config.CSKH_LINK)]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_back_to_main_menu_markup() -> InlineKeyboardMarkup:
    """Creates a simple keyboard with a 'Back to Main Menu' button."""
    keyboard = [[InlineKeyboardButton(RESPONSE_MESSAGES["back_to_menu_button"], callback_data='back_to_main_menu')]]
    return InlineKeyboardMarkup(keyboard)

def create_cancel_keyboard() -> InlineKeyboardMarkup:
    """Creates a keyboard with a single 'Cancel' button."""
    keyboard = [[InlineKeyboardButton("Hủy bỏ", callback_data='cancel')]]
    return InlineKeyboardMarkup(keyboard)

# --- Promotion Flow Keyboards ---

def create_promo_menu_markup() -> InlineKeyboardMarkup:
    """Creates the promotions selection menu keyboard."""
    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES["promo_kl001_button"], callback_data='promo_KL001')],
        [InlineKeyboardButton(RESPONSE_MESSAGES["promo_kl006_button"], callback_data='promo_KL006')],
        [InlineKeyboardButton(RESPONSE_MESSAGES["promo_kl007_button"], callback_data='promo_KL007')],
        [InlineKeyboardButton(RESPONSE_MESSAGES["promo_app_button"], callback_data='promo_APP_PROMO')],
        [InlineKeyboardButton(RESPONSE_MESSAGES["back_to_menu_button"], callback_data='back_to_main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_agree_keyboard(promo_code: str) -> InlineKeyboardMarkup:
    """Creates an 'Agree' and 'Back' keyboard for a specific promo."""
    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES["agree_button_text"], callback_data=f'agree_terms:{promo_code}')],
        [InlineKeyboardButton(RESPONSE_MESSAGES["back_to_promo_menu_button_text"], callback_data='show_promo_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_kl006_group_size_keyboard() -> InlineKeyboardMarkup:
    """Creates keyboard for selecting KL006 group size."""
    keyboard = [
        [InlineKeyboardButton("Nhóm 3 thành viên", callback_data='kl006_select_group:3')],
        [InlineKeyboardButton("Nhóm 5 thành viên", callback_data='kl006_select_group:5')],
        [InlineKeyboardButton(RESPONSE_MESSAGES["back_to_promo_menu_button_text"], callback_data='show_promo_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_app_promo_image_confirm_keyboard() -> InlineKeyboardMarkup:
    """Creates 'Yes/No' keyboard for app promo image confirmation."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Có ảnh", callback_data='app_promo_has_image:yes'),
            InlineKeyboardButton("❌ Không có ảnh", callback_data='app_promo_has_image:no')
        ],
        [InlineKeyboardButton(RESPONSE_MESSAGES["back_to_promo_menu_button_text"], callback_data='show_promo_menu')],
    ]
    return InlineKeyboardMarkup(keyboard)


# --- Sharing Feature Keyboards ---

def create_sharing_menu_markup(show_claim_button: bool = True) -> InlineKeyboardMarkup:
    """
    Tạo bàn phím cho menu chia sẻ.

    Args:
        show_claim_button (bool): True nếu muốn hiển thị nút "Nhận thưởng".
                                  Mặc định là True.
    """
    keyboard = []

    # Chỉ thêm nút "Nhận thưởng" nếu điều kiện cho phép
    if show_claim_button:
        keyboard.append([
            InlineKeyboardButton(RESPONSE_MESSAGES["request_code_reward_button"], callback_data='share_request_reward')
        ])

    # Các nút còn lại luôn được thêm vào
    keyboard.append([
        InlineKeyboardButton(RESPONSE_MESSAGES["get_my_share_link_button"], callback_data='share_get_link')
    ])
    keyboard.append([
        InlineKeyboardButton(RESPONSE_MESSAGES["back_to_menu_button"], callback_data='back_to_main_menu')
    ])

    return InlineKeyboardMarkup(keyboard)


# --- Admin Interaction Keyboards ---

def create_admin_promo_buttons(claim_id: int, user_id: int, promo_code: str,usernames: list = None) -> InlineKeyboardMarkup:
    """Creates the standard processing buttons for a promo claim."""
    buttons = []
    # Add promo-specific buttons
    if promo_code == 'KL001':
        buttons.extend([
            [
                InlineKeyboardButton("❌ Sai ID", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:sai_id"),
                InlineKeyboardButton("✅ Thành Công", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:thanh_cong")
            ],
            [
                InlineKeyboardButton("🔗 Chưa LK NH", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:CLKNH"),
                InlineKeyboardButton("📞 Sai TT (CSKH)", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:SaiTT")
            ],
            [
                InlineKeyboardButton("🚫 Đã nhận KM001", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:kl001_da_nhan"),
                InlineKeyboardButton("🌐 Trùng IP", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:trung_ip")
            ],
            [
                InlineKeyboardButton("💰 Chưa nạp", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:chua_nap"),
                InlineKeyboardButton("💸 Nạp không đủ", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:khong_du")
            ]
        ])
    elif promo_code == 'APP_PROMO':
        buttons.extend([
            [
                InlineKeyboardButton("❌ Sai ID", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:sai_id"),
                InlineKeyboardButton("✅ Thành Công", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:thanh_cong")
            ],
            [
                InlineKeyboardButton("🔗 Chưa LK NH", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:CLKNH"),
                InlineKeyboardButton("📞 Sai TT (CSKH)", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:SaiTT")
            ],
            [
                InlineKeyboardButton("🚫 Đã nhận KM App", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:app_promo_dn"),
                InlineKeyboardButton("🖼️ Y/c hình ảnh", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:app_promo_ha")
            ],
            [
                InlineKeyboardButton("🌐 Trùng IP (App)", callback_data=f"admin_response:{claim_id}:{user_id}:{promo_code}:app_promo_ip")
            ]
        ])
    elif promo_code == 'KL006':
        for idx, uname in enumerate(usernames):
            display_name = uname[:10] + '...' if len(uname) > 10 else uname

        # ✅ ĐÃ BỎ prefix 'kl006_' ở phần action:
            row = [
                InlineKeyboardButton(
                    f"❌ Sai ID: {display_name}",
                    callback_data=f"admin_kl006:{claim_id}:{user_id}:{idx}:sai_id_user"
                ),
                InlineKeyboardButton(
                    f"💸 Cược <3k: {display_name}",
                    callback_data=f"admin_kl006:{claim_id}:{user_id}:{idx}:cuoc_khong_du_user"
                )
            ]
            buttons.append(row)

        # Dòng phân cách
            buttons.append([InlineKeyboardButton("—" * 20, callback_data='ignore')])

    # ✅ Các nút nhóm, action cũng KHÔNG có prefix 'kl006_':
        buttons.append([
            InlineKeyboardButton(
                "📉 Tổng cược nhóm <20k",
                callback_data=f"admin_kl006:{claim_id}:{user_id}:GROUP:khong_du_tong_diem"
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                "🚫 Nhóm đã nhận KM hôm nay",
                callback_data=f"admin_kl006:{claim_id}:{user_id}:GROUP:da_nhan"
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                "📝 Nhóm chưa đăng ký",
                callback_data=f"admin_kl006:{claim_id}:{user_id}:GROUP:nhom_chua_dk"
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                "✅ Thành Công (Duyệt cho cả nhóm)",
                callback_data=f"admin_kl006:{claim_id}:{user_id}:GROUP:thanh_cong"
            )
        ])

    elif promo_code == 'KL007':
        buttons.extend([
            [InlineKeyboardButton("❌ Sai ID", callback_data=f"admin_response:{claim_id}:{user_id}:KL007:sai_id")],
            [InlineKeyboardButton("🎫 Không có vé cược", callback_data=f"admin_response:{claim_id}:{user_id}:KL007:khong_co_ve_kl007")],
            [InlineKeyboardButton("🚫 Đã nhận KM007 hôm nay", callback_data=f"admin_response:{claim_id}:{user_id}:KL007:kl007_da_nhan")]
        ])
    return InlineKeyboardMarkup(buttons)


def create_admin_share_reward_buttons(claim_id: int, user_id: int, milestone: int) -> InlineKeyboardMarkup:
    """Creates processing buttons for a share reward claim."""
    keyboard = [
        [
            InlineKeyboardButton("❌ Sai ID", callback_data=f"admin_share_resp:{claim_id}:{user_id}:{milestone}:sai_id"),
            InlineKeyboardButton("✅ Thành Công", callback_data=f"admin_share_resp:{claim_id}:{user_id}:{milestone}:approved")
        ],
        [InlineKeyboardButton("📞 Liên hệ CSKH", callback_data=f"admin_share_resp:{claim_id}:{user_id}:{milestone}:cskh")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_customer_response_keyboard(promo_code: str = None) -> InlineKeyboardMarkup:
    """Creates a simple keyboard for user to return to main menu after receiving admin response."""
    keyboard = [[InlineKeyboardButton(RESPONSE_MESSAGES["back_to_menu_button"], callback_data='back_to_main_menu')]]
    return InlineKeyboardMarkup(keyboard)

def create_transaction_menu_markup() -> InlineKeyboardMarkup:
    """Tạo bàn phím cho menu chọn Nạp hoặc Rút."""
    keyboard = [
        [
            InlineKeyboardButton(RESPONSE_MESSAGES["transaction_deposit_button"], callback_data='transaction_deposit'),
            InlineKeyboardButton(RESPONSE_MESSAGES["transaction_withdraw_button"], callback_data='transaction_withdraw')
        ],
        [InlineKeyboardButton(RESPONSE_MESSAGES["back_to_menu_button"], callback_data='back_to_main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_admin_deposit_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Tạo bàn phím xử lý cho yêu cầu hỗ trợ nạp tiền của admin."""
    # Chúng ta không cần claim_id vì yêu cầu nạp tiền không được lưu trữ lâu dài
    # Ta sẽ dùng user_id để định danh.

    # Định nghĩa callback_data với một prefix riêng: `admin_deposit:`
    # Format: admin_deposit:<user_id>:<action>

    keyboard = [
        [
            InlineKeyboardButton("✅ Thành công", callback_data=f"admin_deposit:{user_id}:thanh_cong"),
            InlineKeyboardButton("❌ Sai ID", callback_data=f"admin_deposit:{user_id}:sai_id")
        ],
        [
            InlineKeyboardButton("💸 Lên trang khác", callback_data=f"admin_deposit:{user_id}:da_len_trang_khac"),
            InlineKeyboardButton("🚫 Không phải CT", callback_data=f"admin_deposit:{user_id}:khong_phai_cua_chung_toi")
        ],
        [
            InlineKeyboardButton("🧾 HĐ không đúng", callback_data=f"admin_deposit:{user_id}:hoa_don_khong_dung"),
            InlineKeyboardButton("⏳ Chưa nhận tiền", callback_data=f"admin_deposit:{user_id}:chua_nhan_duoc_tien")
        ],
        [
            InlineKeyboardButton("🔄 Làm lại lệnh", callback_data=f"admin_deposit:{user_id}:lam_lai_lenh"),
            InlineKeyboardButton("📈 Đã lên điểm", callback_data=f"admin_deposit:{user_id}:da_len_diem")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_admin_withdraw_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Tạo bàn phím xử lý cho yêu cầu hỗ trợ rút tiền của admin."""
    # Sử dụng prefix 'admin_withdraw:' để phân biệt
    # Format: admin_withdraw:<user_id>:<action>

    keyboard = [
        [
            InlineKeyboardButton("✅ Thành công", callback_data=f"admin_withdraw:{user_id}:thanh_cong"),
            InlineKeyboardButton("🧾 Gửi HĐ", callback_data=f"admin_withdraw:{user_id}:gui_hd")
        ],
        [
            InlineKeyboardButton("❌ Sai TT", callback_data=f"admin_withdraw:{user_id}:sai_tt"),
            InlineKeyboardButton("📈 Y/c sao kê", callback_data=f"admin_withdraw:{user_id}:yeu_cau_sao_ke")
        ],
        [
            InlineKeyboardButton("🛠️ Bảo trì", callback_data=f"admin_withdraw:{user_id}:bao_tri"),
            InlineKeyboardButton("📞 CSKH", callback_data=f"admin_withdraw:{user_id}:cskh")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
