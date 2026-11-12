import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import BOT_TOKEN, ADMIN_ID, REQUIRED_CHANNEL, VIP_PRICES
from database import db

logging.basicConfig(level=logging.INFO)

# === TUGMALAR ===
main_kb = ReplyKeyboardMarkup([
    ["🎬 Kino izlash"],
    ["⭐️ VIP olish"],
    ["📕 Yordam"]
], resize_keyboard=True)

admin_kb = ReplyKeyboardMarkup([
    ["🎬 Kino izlash", "➕ Kino qo'shish"],
    ["📕 Kinolar ro'yxati", "📊 Statistika"],
    ["💳 Bank kartalari"],
    ["🔙 Asosiy menyu"]
], resize_keyboard=True)

def is_admin(user_id):
    return user_id == ADMIN_ID

async def is_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id):
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status not in ["left", "kicked"]
    except Exception as e:
        print(f"Obuna tekshirish xatosi: {e}")
        return False

# === /start BUYURUG'I ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.add_user(user_id)

    if not db.is_vip_user(user_id) and not is_admin(user_id):
        if not await is_subscribed(context, user_id):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Kanalga qo'shilish", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}")],
                [InlineKeyboardButton("🔄 Tekshirish", callback_data="check_sub")]
            ])
            await update.message.reply_text(
                "⚠️ Botdan foydalanish uchun kanalimizga a'zo bo'ling!",
                reply_markup=keyboard
            )
            return

    if await is_subscribed(context, user_id):
        db.add_channel_member(user_id)

    if is_admin(user_id):
        await update.message.reply_text("👋 Assalomu alaykum, Admin!", reply_markup=admin_kb)
    else:
        await update.message.reply_text("👋 Assalomu alaykum! Kino kodini kiriting:", reply_markup=main_kb)

# === CALLBACK TUGMALAR ===
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    await query.answer()

    if data == "check_sub":
        if await is_subscribed(context, user_id):
            db.add_channel_member(user_id)
            await query.edit_message_text("✅ Obuna tasdiqlandi! Endi /start ni yozing.")
        else:
            await query.answer("❌ Siz hali kanalga a'zo bo'lmagansiz!", show_alert=True)

    elif data.startswith("ep_"):
        ep_id = int(data.split("_")[1])
        c = db.conn.cursor()
        c.execute("SELECT * FROM episodes WHERE id=?", (ep_id,))
        ep = c.fetchone()
        if ep:
            await context.bot.send_video(
                chat_id=user_id,
                video=ep[3],
                caption=f"🎬 {ep[2]}-qism"
            )

    elif data.startswith("vip_"):
        period = data.split("_")[1]
        months_map = {"1oy": 1, "2oy": 2, "3oy": 3, "6oy": 6, "12oy": 12}
        months = months_map.get(period)
        if months:
            db.set_vip(user_id, months)
            await query.edit_message_text(f"✅ Tabriklaymiz! {months} oylik VIP faollashtirildi!")

# === VIP MENYUSI ===
async def vip_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if db.is_vip_user(user_id):
        await update.message.reply_text("⭐️ Siz allaqachon VIP a'zosiz!")
        return

    cards = db.get_cards()
    card_text = "\n💳 To'lov uchun kartalar:\n"
    if cards:
        for c in cards:
            card_text += f"• {c[2]}: {c[1]}\n"
    else:
        card_text += "Hozircha karta qo'yilmagan\n"

    keyboard = []
    for period, price in VIP_PRICES.items():
        keyboard.append([InlineKeyboardButton(f"{period} — {price:,} so'm", callback_data=f"vip_{period}")])

    await update.message.reply_text(
        f"⭐️ VIP ga o'ting!\n{card_text}\nMuddatni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# === XABARLARNI QAYTA ISHLASH ===
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text or ""
    state = context.user_data.get("state")

    # === ASOSIY MENYU TUGMALARI ===
    if text == "🔙 Asosiy menyu":
        context.user_data.clear()
        await update.message.reply_text("Bosh menyu ⬅️", reply_markup=main_kb)
        return

    if text == "🎬 Kino izlash":
        await update.message.reply_text("Kino kodini kiriting:")
        return

    if text == "⭐️ VIP olish":
        await vip_menu(update, context)
        return

    if text == "📕 Yordam":
        await update.message.reply_text(
            "📖 Foydalanish qo'llanmasi:\n"
            "• Kino kodini yozing → kino topiladi\n"
            "• Qism raqamli tugmani bosing → video yuklanadi\n"
            "• VIP olish → reklamasiz va obunasiz foydalaning"
        )
        return

    # === ADMIN MENYUSI ===
    if is_admin(user_id):
        if text == "➕ Kino qo'shish":
            await update.message.reply_text("Yangi kino kodini kiriting:")
            context.user_data["state"] = "add_code"
            return

        if text == "📕 Kinolar ro'yxati":
            movies = db.list_movies()
            if not movies:
                await update.message.reply_text("Hali hech qanday kino qo'shilmagan!")
                return
            msg = "📕 Kinolar ro'yxati:\n\n"
            for m in movies:
                msg += f"🎬 Kod: {m[1]}\nNomi: {m[2]}\nHolati: {m[3]}\nKo'rilgan: {m[4]} marta\n"
                msg += f"/del{m[0]} — O'chirish | /status{m[0]} — Holatni o'zgartirish\n\n"
            await update.message.reply_text(msg)
            return

        if text == "📊 Statistika":
            total_users = len(db.conn.cursor().execute("SELECT * FROM users").fetchall())
            total_movies = len(db.conn.cursor().execute("SELECT * FROM movies").fetchall())
            vip_count = len(db.conn.cursor().execute("SELECT * FROM users WHERE is_vip=1").fetchall())
            channel_count = db.count_channel_members()
            await update.message.reply_text(
                f"📊 Bot statistikasi:\n"
                f"• Jami foydalanuvchilar: {total_users}\n"
                f"• Kanalga a'zo bo'lganlar: {channel_count}\n"
                f"• Kinolar soni: {total_movies}\n"
                f"• VIP a'zolar: {vip_count}"
            )
            return

        if text == "💳 Bank kartalari":
            cards = db.get_cards()
            msg = "💳 Bank kartalari ro'yxati:\n\n"
            if cards:
                for c in cards:
                    msg += f"ID{c[0]} — {c[2]}: {c[1]}\n/delcard{c[0]} — O'chirish\n"
            else:
                msg += "Hali hech qanday karta qo'shilmagan!\nYangi karta qo'shish: /addcard 8600123456789012 Agrobank"
            await update.message.reply_text(msg)
            return

        # Admin buyruqlari
        if text.startswith("/delcard"):
            try:
                card_id = int(text.split()[0][8:])
                db.delete_card(card_id)
                await update.message.reply_text("✅ Karta o'chirildi!")
            except:
                await update.message.reply_text("❌ Noto'g'ri buyruq!")
            return

        if text.startswith("/addcard"):
            parts = text.split(" ", 2)
            if len(parts) >= 3:
                _, number, bank = parts
                db.add_card(number, bank)
                await update.message.reply_text(f"✅ Karta qo'shildi!\n{bank}: {number}")
            else:
                await update.message.reply_text("❌ Noto'g'ri format! Misol: /addcard 8600123456789012 Agrobank")
            return

        if text.startswith("/del"):
            try:
                movie_id = int(text[4:])
                db.delete_movie(movie_id)
                await update.message.reply_text("✅ Kino o'chirildi!")
            except:
                await update.message.reply_text("❌ Kino topilmadi!")
            return

        if text.startswith("/status"):
            parts = text.split()
            if len(parts) == 2:
                try:
                    movie_id = int(parts[0][7:])
                    status = parts[1]
                    if status in ["davom", "tugagan"]:
                        status_text = "davom etmoqda" if status == "davom" else "tugagan"
                        db.update_status(movie_id, status_text)
                        await update.message.reply_text(f"✅ Kino holati o'zgartirildi: {status_text}")
                except:
                    await update.message.reply_text("❌ Xato!")
            return

        # Kino qo'shish jarayoni
        if state == "add_code":
            context.user_data["code"] = text
            context.user_data["state"] = "add_name"
            await update.message.reply_text("✅ Kod qabul qilindi! Endi kino nomini kiriting:")
            return

        if state == "add_name":
            movie_id = db.add_movie(context.user_data["code"], text)
            if movie_id:
                context.user_data["movie_id"] = movie_id
                context.user_data["episode_num"] = 1
                context.user_data["state"] = "add_episode"
                await update.message.reply_text(
                    f"✅ Kino saqlandi!\nKino ID: {movie_id}\n\nEndi {1}-qism videosini yuklang:"
                )
            else:
                await update.message.reply_text("❌ Bu kodli kino allaqachon mavjud!")
                context.user_data.clear()
            return

        if state == "add_episode" and update.message.video:
            movie_id = context.user_data["movie_id"]
            ep_num = context.user_data["episode_num"]
            file_id = update.message.video.file_id
            db.add_episode(movie_id, ep_num, file_id)
            context.user_data["episode_num"] += 1
            await update.message.reply_text(
                f"✅ {ep_num}-qism saqlandi!\nKeyingi qismni yuklang yoki /tugat deb yozing:"
            )
            return

        if text == "/tugat":
            context.user_data.clear()
            await update.message.reply_text("✅ Kino qo'shish yakunlandi!")
            return

    # === ODDIY FOYDALANUVCHI: KINO IZLASH ===
    movie = db.get_movie_by_code(text.strip())
    if movie:
        db.add_view(movie[0])
        episodes = db.get_episodes(movie[0])
        msg_text = f"🎬 {movie[2]}\n📅 Holat: {movie[3]}\n👁️ Ko'rilgan: {movie[4]} marta"

        if episodes:
            kb = []
            for ep in episodes:
                kb.append([InlineKeyboardButton(f"📎 {ep[2]}-qism", callback_data=f"ep_{ep[0]}")])
            await update.message.reply_text(msg_text, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await update.message.reply_text(msg_text + "\n\n⚠️ Bu kino uchun qismlar yuklanmagan")

# === XATO USHLASH ===
async def error_handler(update, context):
    print(f"Xato: {context.error}")

# === BOTNI ISHGA TUSHIRISH ===
def main():
    try:
        print("🔄 Bot yuklanmoqda...")
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(callback_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        app.add_handler(MessageHandler(filters.VIDEO, message_handler))
        app.add_error_handler(error_handler)

        print("✅ Bot muvaffaqiyatli ishga tushdi!")
        app.run_polling(drop_pending_updates=True)

    except Exception as e:
        print(f"❌ Dastur xatosi: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
