import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import BOT_TOKEN, ADMIN_ID, REQUIRED_CHANNEL, VIP_PRICES
from database import db

logging.basicConfig(level=logging.INFO)

# === Yordamchi funksiyalar ===
def is_admin(user_id):
    return user_id == ADMIN_ID

async def is_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id):
    """Kanala obuna bo'lganligini tekshirish"""
    try:
        status = await context.bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return status.status not in ["left", "kicked"]
    except:
        return False

# === Asosiy menyu tugmalari ===
main_keyboard = ReplyKeyboardMarkup([
    ["🎬 Kino izlash"],
    ["⭐️ VIP olish"],
    ["📕 Yordam"]
], resize_keyboard=True)

admin_keyboard = ReplyKeyboardMarkup([
    ["🎬 Kino izlash", "➕ Kino qo'shish"],
    ["📕 Kinolar ro'yxati", "📊 Statistika"],
    ["💳 Bank kartalari", "⚙️ Sozlamalar"],
    ["🔙 Asosiy menyu"]
], resize_keyboard=True)

# === /start buyrug'i ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.add_user(user_id)
    
    # VIP bo'lmagan va admin bo'lmaganlar uchun obuna tekshiruvi
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
    
    # Obuna bo'lganlarni bazaga qo'shish
    if await is_subscribed(context, user_id):
        db.add_channel_member(user_id)
    
    vip_text = "⭐️ Siz VIP a'zosiz!" if db.is_vip_user(user_id) else ""
    if is_admin(user_id):
        await update.message.reply_text(
            f"Assalomu alaykum, Admin! 👮‍♂️\n{vip_text}\nQuyidagi menyudan foydalaning:",
            reply_markup=admin_keyboard
        )
    else:
        await update.message.reply_text(
            f"Assalomu alaykum! 👋\nKino kodini yozing yoki menyudan tanlang.\n{vip_text}",
            reply_markup=main_keyboard
        )

# === Obuna tekshirish tugmasi ===
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    
    if await is_subscribed(context, user_id):
        db.add_channel_member(user_id)
        await query.edit_message_text("✅ Obuna tasdiqlandi! Endi /start buyrug'ini yozing.")
    else:
        await query.answer("❌ Siz hali kanalga a'zo bo'lmagansiz!", show_alert=True)

# === Kino izlash ===
async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    movie = db.get_movie_by_code(code)
    
    if not movie:
        await update.message.reply_text("❌ Bunday kodli kino topilmadi!")
        return
    
    # Ko'rishlar sonini oshirish
    db.increment_views(movie[0])
    episodes = db.get_episodes(movie[0])
    
    text = f"🎬 {movie[2]}\n📅 Holat: {movie[3]}\n👁️ Ko'rilgan: {movie[4]} ta"
    
    if episodes:
        keyboard = []
        for ep in episodes:
            keyboard.append([InlineKeyboardButton(f"📎 {ep[2]}-qism", callback_data=f"ep_{ep[0]}")])
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text + "\n\n⚠️ Bu kino uchun qismlar yuklanmagan")

# === Qismni yuborish ===
async def send_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    
    if data.startswith("ep_"):
        ep_id = int(data.split("_")[1])
        c = db.conn.cursor()
        c.execute("SELECT * FROM episodes WHERE id=?", (ep_id,))
        ep = c.fetchone()
        if ep:
            await context.bot.send_video(
                chat_id=update.effective_user.id,
                video=ep[3],
                caption=f"🎬 {ep[2]}-qism"
            )

# === VIP sotib olish menyusi ===
async def vip_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if db.is_vip_user(user_id):
        await update.message.reply_text("⭐️ Siz allaqachon VIP a'zosiz!")
        return
    
    cards = db.get_bank_cards()
    card_text = "\n💳 To'lov quyidagi kartaga amalga oshiring:\n"
    if cards:
        for c in cards:
            card_text += f"• {c[2]}: {c[1]}\n"
    else:
        card_text += "Hozircha karta qo'yilmagan. Keyinroq urinib ko'ring."
    
    keyboard = [
        [InlineKeyboardButton(f"1 oylik — {VIP_PRICES['1oy']} so'm", callback_data="vip_1oy")],
        [InlineKeyboardButton(f"2 oylik — {VIP_PRICES['2oy']} so'm", callback_data="vip_2oy")],
        [InlineKeyboardButton(f"3 oylik — {VIP_PRICES['3oy']} so'm", callback_data="vip_3oy")],
        [InlineKeyboardButton(f"6 oylik — {VIP_PRICES['6oy']} so'm", callback_data="vip_6oy")],
        [InlineKeyboardButton(f"12 oylik — {VIP_PRICES['12oy']} so'm", callback_data="vip_12oy")],
    ]
    await update.message.reply_text(
        f"⭐️ VIP ga o'ting!\nFoydalanish muddati davomida majburiy obuna talab qilinmaydi.\n{card_text}\nMuddatni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# === Admin: Kino qo'shish ===
async def add_movie_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text("Yangi kino kodini kiriting:")
    context.user_data['state'] = "add_movie_code"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text or ""
    
    # === Boshqaruv holatlari ===
    state = context.user_data.get('state')
    
    # Kino izlash tugmasi bosilganda
    if text == "🎬 Kino izlash":
        await update.message.reply_text("Kino kodini kiriting:")
        return
    
    # VIP olish
    if text == "⭐️ VIP olish":
        await vip_menu(update, context)
        return
    
    # Yordam
    if text == "📕 Yordam":
        await update.message.reply_text(
            "📖 Yordam:\n"
            "• Kino kodini yozing → kino chiqadi\n"
            "• Qism tugmasini bosing → video yuklanadi\n"
            "• VIP olish → reklamasiz va obunasiz foydalaning"
        )
        return
    
    # === ADMIN MENYUSI ===
    if is_admin(user_id):
        if text == "🔙 Asosiy menyu":
            await update.message.reply_text("Bosh menyu ⬅️", reply_markup=main_keyboard)
            return
        
        if text == "➕ Kino qo'shish":
            await update.message.reply_text("Kino kodini kiriting:")
            context.user_data['state'] = "add_movie_code"
            return
        
        if text == "📕 Kinolar ro'yxati":
            movies = db.list_movies()
            if not movies:
                await update.message.reply_text("Hech qanday kino yo'q")
                return
            text_list = "📕 Kinolar:\n"
            for m in movies:
                text_list += f"• {m[1]} — {m[2]} [{m[3]}] | Ko'rilgan: {m[4]}\n"
                text_list += f"    /del{m[0]}  /status{m[0]}_tugagan  /status{m[0]}_davom\n"
            await update.message.reply_text(text_list)
            return
        
        if text == "📊 Statistika":
            total_users = len(db.conn.cursor().execute("SELECT * FROM users").fetchall())
            total_movies = len(db.conn.cursor().execute("SELECT * FROM movies").fetchall())
            channel_members = db.count_channel_members()
            vip_users = len(db.conn.cursor().execute("SELECT * FROM users WHERE is_vip=1").fetchall())
            await update.message.reply_text(
                f"📊 Statistika:\n"
                f"• Foydalanuvchilar: {total_users}\n"
                f"• Kanal a'zolari: {channel_members}\n"
                f"• Kinolar soni: {total_movies}\n"
                f"• VIP a'zolar: {vip_users}"
            )
            return
        
        if text == "💳 Bank kartalari":
