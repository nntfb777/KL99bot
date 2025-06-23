import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
import database, config
from texts import RESPONSE_MESSAGES
from .core import _remove_buttons, back_to_menu_handler, cancel

logger = logging.getLogger(__name__)

# Đảm bảo các trạng thái này được định nghĩa chính xác
SHOW_SHARE_MENU, AWAIT_USERNAME_FOR_SHARE_REWARD = range(2)

# last_admin_share_msg_id và last_admin_share_chat_id cần được định nghĩa ở cấp độ module nếu được sử dụng
# Ví dụ:
last_admin_share_msg_id = {}
last_admin_share_chat_id = {}

async def share_code_entry_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.message: await _remove_buttons(query)

    user_id = query.from_user.id
    user_s_data = database.get_user_data(user_id)
    share_count = user_s_data.get("share_count", 0)

    claimed_milestones = [int(k) for k in user_s_data.get("claimed_share_milestones", {}).keys()]

    next_milestone_val = RESPONSE_MESSAGES["all_milestones_achieved_text"]
    needed_shares_val = "N/A"

    # Tìm mốc thưởng tiếp theo
    found_next_milestone = False
    for ms in config.SHARE_MILESTONES:
        if ms not in claimed_milestones:
            next_milestone_val = f"{ms} lượt"
            needed_shares_val = max(0, ms - share_count)
            found_next_milestone = True
            break

    intro_text = ""
    if found_next_milestone:
        intro_text = RESPONSE_MESSAGES["share_code_intro"].format(
            share_count=share_count,
            next_milestone=next_milestone_val,
            needed_shares=needed_shares_val
        )
    else:
        # Nếu đã đạt tất cả các mốc
        intro_text = RESPONSE_MESSAGES["share_code_intro_no_shares_all_claimed"].format( # Đảm bảo key này có trong texts.py
            share_count=share_count
        )


    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES["get_my_share_link_button"], callback_data='get_my_share_link')],
    ]

    # Chỉ hiển thị nút "Nhận Code thưởng" nếu có mốc chưa nhận
    # Nút này sẽ dẫn đến request_code_reward_callback để chọn mốc
    if found_next_milestone and needed_shares_val <= 0: # Chỉ hiển thị khi đã đủ lượt chia sẻ cho mốc tiếp theo
        keyboard.append([InlineKeyboardButton(RESPONSE_MESSAGES["request_code_reward_button"], callback_data='request_code_reward')])
    elif not found_next_milestone: # Đã nhận tất cả các mốc
        # Nút kiểm tra trạng thái thưởng (nếu có)
        keyboard.append([InlineKeyboardButton(RESPONSE_MESSAGES["check_reward_button_text"], callback_data='check_reward_status')])

    keyboard.append([InlineKeyboardButton(RESPONSE_MESSAGES["back_to_menu_button"], callback_data='back_to_menu')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=intro_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return SHOW_SHARE_MENU

async def share_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hiển thị menu Chia sẻ nhận thưởng."""
    query = update.callback_query
    if query:
        await query.answer()
        if query.message:
            from .core import _remove_buttons
            await _remove_buttons(query)

    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES["share_request_code_button"], callback_data='request_code_reward')],
        [InlineKeyboardButton(RESPONSE_MESSAGES["share_get_link_button"], callback_data='get_my_share_link')],
        # Bạn có thể thêm nút kiểm tra trạng thái thưởng nếu có tính năng này
        # [InlineKeyboardButton(RESPONSE_MESSAGES["share_reward_status_button"], callback_data='check_share_reward_status')],
        [InlineKeyboardButton(RESPONSE_MESSAGES["back_to_menu_button"], callback_data='back_to_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_chat.send_message(
        RESPONSE_MESSAGES["share_menu_intro"], # Đảm bảo khóa này có trong texts.py của bạn
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN_V2
    )

# Hàm này sẽ được giữ lại và là hàm xử lý username chính
async def process_username_for_share_reward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    game_username = update.message.text.strip()
    milestone = context.user_data.get('share_reward_milestone') # Lấy từ context.user_data

    if not milestone:
        await update.message.reply_text("Có lỗi xảy ra. Vui lòng thử lại từ đầu.")
        return ConversationHandler.END

    admin_text = (f"🔗 *YÊU CẦU NHẬN THƯỞNG CHIA SẺ MỚI* 🔗\n\n" # Đã sửa double backslash
                  f"👤 Khách: {user.mention_markdown_v2()} `({user.id})`\n"
                  f"🎮 Tên game: `{escape_markdown(game_username, version=2)}`\n"
                  f"🏆 Mốc thưởng: *{escape_markdown(str(milestone), version=2)} lượt*")

    keyboard = [[
        InlineKeyboardButton("✅ Duyệt", callback_data=f"admin_share_resp:{user.id}:approve:{milestone}:{game_username}"),
        InlineKeyboardButton("❌ Sai ID", callback_data=f"admin_share_resp:{user.id}:sai_id:{milestone}:{game_username}"),
        InlineKeyboardButton("ℹ️ CSKH", callback_data=f"admin_share_resp:{user.id}:contact_cskh:{milestone}:{game_username}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        admin_msg = await context.bot.send_message(
            chat_id=config.ID_GROUP_PROMO, # Gửi đến nhóm admin hoặc nhóm promo
            text=admin_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        # LƯU TRỮ message_id CỦA TIN NHẮN ADMIN VÀO DATABASE
        database.update_user_data(user.id, {
            'last_admin_share_msg_id': admin_msg.message_id,
            'last_admin_share_chat_id': config.ID_GROUP_PROMO
        })

        # Cập nhật trạng thái "pending" vào database
        user_s_data = database.get_user_data(user.id)
        pending_milestones = user_s_data.get("pending_share_milestones", {})
        pending_milestones[str(milestone)] = True # Đánh dấu mốc này đang chờ xử lý
        database.update_user_data(user.id, {'pending_share_milestones': pending_milestones})

        await update.message.reply_text(RESPONSE_MESSAGES["share_reward_request_sent"].format(milestone=milestone, game_username=game_username))
    except Exception as e:
        logger.error(f"Lỗi khi gửi yêu cầu thưởng chia sẻ đến admin: {e}")
        await update.message.reply_text(RESPONSE_MESSAGES["error_sending_request"])

    return ConversationHandler.END

# Hàm process_share_code_username đã được xóa khỏi đây vì trùng lặp chức năng.

async def get_my_share_link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _remove_buttons(query)

    user_id = query.from_user.id
    user_data = database.get_user_data(user_id)
    referral_code = user_data.get("referral_code")

    if not referral_code:
        logger.warning(f"Người dùng {user_id} yêu cầu link chia sẻ nhưng không có referral_code.")
        await query.message.reply_text(RESPONSE_MESSAGES["error_no_referral_code"])
        # Quay lại menu chia sẻ
        return await share_code_entry_point(update, context) 

    bot_info = await context.bot.get_me()
    if not bot_info or not bot_info.username:
        logger.error("Không thể lấy thông tin username của bot.")
        await query.message.reply_text(RESPONSE_MESSAGES["error_getting_bot_info"])
        # Quay lại menu chia sẻ
        return await share_code_entry_point(update, context)

    share_link = f"https://t.me/{bot_info.username}?start=ref_{referral_code}"
    await query.message.reply_text(
        RESPONSE_MESSAGES["my_share_link_message"].format(share_link=escape_markdown(share_link, version=2)),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    # Sau khi gửi link, quay lại menu chia sẻ
    return await share_code_entry_point(update, context)

async def request_code_reward_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _remove_buttons(query)

    user_id = query.from_user.id
    user_s_data = database.get_user_data(user_id)
    share_count = user_s_data.get("share_count", 0)
    claimed_milestones = [int(k) for k in user_s_data.get("claimed_share_milestones", {}).keys()]
    pending_milestones = user_s_data.get("pending_share_milestones", {})

    eligible_milestones = []
    for ms in config.SHARE_MILESTONES:
        if ms not in claimed_milestones and ms <= share_count and str(ms) not in pending_milestones:
            eligible_milestones.append(ms)
    
    if not eligible_milestones:
        if any(str(ms) in pending_milestones for ms in config.SHARE_MILESTONES):
            # Tìm mốc đang chờ xử lý
            current_pending_milestone = next(iter(pending_milestones.keys()), None)
            await query.message.reply_text(RESPONSE_MESSAGES["pending_claim_exists"].format(milestone=current_pending_milestone))
        else:
            needed_shares = 0
            found_next_potential = False
            for ms in config.SHARE_MILESTONES:
                if ms not in claimed_milestones:
                    needed_shares = max(0, ms - share_count)
                    found_next_potential = True
                    break
            if found_next_potential:
                # Nếu có mốc tiếp theo nhưng chưa đủ lượt
                await query.message.reply_text(RESPONSE_MESSAGES["no_new_milestone_message"].format(
                    needed_more=needed_shares,
                    next_milestone=eligible_milestones[0] if eligible_milestones else "Mốc tiếp theo" # Fallback nếu không tìm thấy
                ))
            else:
                # Đã nhận hết tất cả các mốc và không có mốc nào đang chờ xử lý
                await query.message.reply_text(RESPONSE_MESSAGES["all_milestones_claimed_message"])
        return SHOW_SHARE_MENU # Luôn quay lại menu chia sẻ sau khi hiển thị thông báo

    # Hiển thị các nút mốc thưởng để người dùng chọn
    keyboard = []
    for ms in eligible_milestones:
        keyboard.append([InlineKeyboardButton(f"{ms} lượt", callback_data=f"select_share_reward:{ms}")])
    keyboard.append([InlineKeyboardButton(RESPONSE_MESSAGES["back_to_menu_button"], callback_data='back_to_menu')]) # Hoặc 'sharing' để quay về menu chia sẻ

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        RESPONSE_MESSAGES["select_milestone_for_reward"], # Đảm bảo key này có trong texts.py
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    # Hàm này KHÔNG trả về một trạng thái conversation,
    # mà sẽ hiển thị các nút để select_share_reward_callback làm entry_point
    return SHOW_SHARE_MENU # Quay lại SHOW_SHARE_MENU sau khi hiển thị các nút mốc

async def select_share_reward_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    milestone = int(query.data.split(':')[1])
    context.user_data['share_reward_milestone'] = milestone # CHỈNH SỬA: Lưu mốc đã chọn với key thống nhất

    # Kiểm tra xem tin nhắn có tồn tại trước khi chỉnh sửa
    if query.message:
        try:
            await query.edit_message_text(
                text=RESPONSE_MESSAGES["ask_game_username_for_share_reward"], # Đảm bảo key này có trong texts.py
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as e:
            logger.warning(f"Could not edit message for share reward selection: {e}. Sending new message.")
            await query.message.reply_text(
                text=RESPONSE_MESSAGES["ask_game_username_for_share_reward"],
                parse_mode=ParseMode.MARKDOWN_V2
            )
    else:
        await update.effective_chat.send_message(
            text=RESPONSE_MESSAGES["ask_game_username_for_share_reward"],
            parse_mode=ParseMode.MARKDOWN_V2
        )
    # CHỈNH SỬA: Trả về trạng thái thống nhất
    return AWAIT_USERNAME_FOR_SHARE_REWARD

# Conversation Handler cho việc yêu cầu code chia sẻ (bắt đầu khi chọn mốc)
share_code_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(select_share_reward_callback, pattern='^select_share_reward:([0-9]+)$')],
    states={
        # Ở trạng thái này, bot sẽ chờ tên game sau khi người dùng đã chọn mốc
        # CHỈNH SỬA: Sử dụng trạng thái và hàm xử lý thống nhất
        AWAIT_USERNAME_FOR_SHARE_REWARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_username_for_share_reward)],
    },
    fallbacks=[
        CallbackQueryHandler(share_menu_callback, pattern='^sharing$'), # Quay lại menu chia sẻ chính
        CommandHandler('cancel', cancel), # Lệnh /cancel
        CallbackQueryHandler(back_to_menu_handler, pattern='^back_to_menu$'), # Quay lại menu chính tổng thể
    ]
)