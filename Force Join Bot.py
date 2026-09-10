# -*- coding: utf-8 -*-
"""
ربات عضویت اجباری تلگرام (Force Join Bot)
------------------------------------------
وقتی کاربر /start می‌زند، ربات بررسی می‌کند که آیا در کانال/گروه(های) تعیین‌شده
عضو هست یا نه. اگر عضو نبود، لینک عضویت را می‌فرستد و اجازه‌ی استفاده از ربات
را نمی‌دهد. کاربر با زدن دکمه‌ی "✅ عضو شدم" دوباره بررسی می‌شود.

نصب پیش‌نیازها:
    pip install python-telegram-bot --upgrade

نکات مهم قبل از اجرا:
    1) ربات را بسازید و توکن را از @BotFather بگیرید.
    2) ربات را در هر کانال/گروهی که می‌خواهید عضویت اجباری کنید، ADMIN کنید
       (حداقل با دسترسی "Add Users" / مشاهده‌ی اعضا) — بدون این کار، ربات
       نمی‌تواند وضعیت عضویت کاربر را چک کند.
    3) اگر کانال/گروه پابلیک است، یوزرنیم آن را با @ در CHANNELS بگذارید
       (مثلا "@my_channel"). اگر پرایوت است، به‌جای یوزرنیم از chat_id عددی
       (مثلا -1001234567890) استفاده کنید و invite_link را دستی بگذارید.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ================== تنظیمات اصلی — این‌ها را عوض کنید ==================

BOT_TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"

# اگه تلگرام فیلتره و به فیلترشکن/پراکسی نیاز دارید، آدرس پراکسی رو اینجا بذارید.
# مثال SOCKS5:  "socks5://127.0.0.1:1080"
# مثال HTTP:    "http://127.0.0.1:8080"
# اگه به پراکسی نیاز ندارید (روی سرور خارج از ایران اجرا می‌کنید)، None بذارید.
PROXY_URL = None  # مثلا: "socks5://127.0.0.1:1080"

# لیست کانال/گروه‌هایی که عضویت در آن‌ها اجباری است.
# chat_id: برای چک کردن عضویت استفاده می‌شود (یوزرنیم پابلیک یا آیدی عددی پرایوت)
# title: اسمی که به کاربر نمایش داده می‌شود
# invite_link: لینکی که روی دکمه می‌رود (برای پابلیک می‌توانید https://t.me/username بگذارید)
CHANNELS = [
    {
        "chat_id": "@your_channel_username",
        "title": "📢 کانال ما",
        "invite_link": "https://t.me/your_channel_username",
    },
    # می‌توانید کانال/گروه دیگری هم اضافه کنید:
    # {
    #     "chat_id": -1001234567890,          # آیدی عددی گروه/کانال پرایوت
    #     "title": "👥 گروه ما",
    #     "invite_link": "https://t.me/+AbCdEfGhIjKlMnOp",  # لینک دعوت پرایوت
    # },
]

# پیامی که بعد از عضویت موفق نمایش داده می‌شود
WELCOME_MESSAGE = "✅ خوش اومدی! عضویتت تایید شد و حالا می‌تونی از ربات استفاده کنی."

# =========================================================================

MEMBER_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.OWNER,
}


async def is_user_member_of_all(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> list:
    """برمی‌گرداند لیستی از کانال‌هایی که کاربر هنوز عضوشان نیست."""
    not_joined = []
    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=ch["chat_id"], user_id=user_id)
            if member.status not in MEMBER_STATUSES:
                not_joined.append(ch)
        except Exception as e:
            # اگر ربات ادمین نباشد یا chat_id اشتباه باشد، این خطا می‌آید
            logger.warning(f"خطا در بررسی عضویت کاربر {user_id} در {ch['chat_id']}: {e}")
            not_joined.append(ch)
    return not_joined


def build_join_keyboard(not_joined_channels: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(ch["title"], url=ch["invite_link"])]
        for ch in not_joined_channels
    ]
    buttons.append([InlineKeyboardButton("✅ عضو شدم", callback_data="check_membership")])
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    not_joined = await is_user_member_of_all(context, user_id)

    if not_joined:
        text = (
            "🚫 برای استفاده از ربات، اول باید در موارد زیر عضو بشی:\n\n"
            "بعد از عضویت، روی دکمه‌ی «✅ عضو شدم» بزن."
        )
        await update.message.reply_text(text, reply_markup=build_join_keyboard(not_joined))
    else:
        await update.message.reply_text(WELCOME_MESSAGE)
        # اینجا می‌تونی منوی اصلی ربات یا هر کار دیگه‌ای رو صدا بزنی


async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    not_joined = await is_user_member_of_all(context, user_id)

    if not_joined:
        await query.answer("❌ هنوز عضو همه‌ی موارد نشدی!", show_alert=True)
        await query.edit_message_reply_markup(reply_markup=build_join_keyboard(not_joined))
    else:
        await query.answer("✅ عضویت تایید شد!")
        await query.edit_message_text(WELCOME_MESSAGE)


def main():
    builder = Application.builder().token(BOT_TOKEN)
    if PROXY_URL:
        # هم برای درخواست‌های عادی و هم برای polling (get_updates) از پراکسی استفاده کن
        builder = builder.proxy(PROXY_URL).get_updates_proxy(PROXY_URL)
    app = builder.build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_membership_callback, pattern="^check_membership$"))

    logger.info("ربات در حال اجراست...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
