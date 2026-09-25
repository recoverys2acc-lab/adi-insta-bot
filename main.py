import json
import logging
import os
import urllib.parse
import threading
import requests
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# ================= CONFIGURATION =================
BOT_TOKEN = "8789950683:AAHOhiJsa2Y5RRksl61rMqmoErNQGAMT7x0"
ADMIN_ID = 8313247547
UPI_ID = "7276052050@fam"
CHANNEL_USERNAME = "@adityaservicesofficial"  
SUPPORT_LINK = f"tg://user?id={ADMIN_ID}"     
ORDERS_FILE = "orders.json"

# LuvSMM Panel API Configuration
SMM_API_URL = "https://luvsmm.com/api/v2"  
SMM_API_KEY = "a2d676468376cdcc9cbc7ee5e0487af9"  # 👈 Aapki LuvSMM API key integrated hai[span_2](start_span)[span_2](end_span)

# LuvSMM Panel Service IDs Mapping (Aapke bataye hue IDs)
SERVICE_IDS = {
    "views": 1137,               # Instagram Views ID[span_3](start_span)[span_3](end_span)
    "likes": 173,                # Instagram Likes ID
    "comments": 1517,            # Instagram Custom Comments ID
    "followers_no_refill": 1300, # Instagram Followers (No Refill) ID
    "followers_guarantee": 4038, # Instagram Followers (Lifetime Guarantee) ID
}

# Flask Server for Render (To keep service alive 24/7)
app = Flask(__name__)

@app.route('/')
def home():
    return "Aditya Services Bot is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ================= HELPER FUNCTIONS =================
def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    try:
        with open(ORDERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_order(order_data):
    orders = load_orders()
    orders.append(order_data)
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4)

async def check_force_join(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
        return False
    except Exception as e:
        print(f"FORCE JOIN ERROR: {e}")
        return False

def get_force_join_keyboard():
    channel_clean = CHANNEL_USERNAME.replace("@", "")
    keyboard = [
        [InlineKeyboardButton("📢 Join Our Official Channel", url=f"https://t.me/{channel_clean}")],
        [InlineKeyboardButton("✅ Verify / I Have Joined", callback_data="check_join")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("👁️ Reel Views", callback_data="service_views"), InlineKeyboardButton("❤️ Likes", callback_data="service_likes")],
        [InlineKeyboardButton("💬 Custom Comments", callback_data="service_comments")],
        [InlineKeyboardButton("👥 Followers (No Refill)", callback_data="service_followers_no_refill")],
        [InlineKeyboardButton("👥 Followers (Lifetime Guarantee)", callback_data="service_followers_guarantee")],
        [InlineKeyboardButton("📋 My Orders", callback_data="my_orders"), InlineKeyboardButton("📞 Support", callback_data="contact_support")]
    ]
    return InlineKeyboardMarkup(keyboard)

def calculate_cost(service, qty):
    if service == "views":
        tiers = [(10000, 19), (50000, 49), (100000, 79), (1000000, 299)]
    elif service == "likes":
        tiers = [(1000, 20), (5000, 60), (10000, 110)]
    elif service == "comments":
        tiers = [(100, 29), (1000, 229), (2000, 399), (4000, 749), (6000, 1099), (8000, 1399), (10000, 1699)]
    elif service == "followers_no_refill":
        tiers = [(500, 149), (1000, 279), (5000, 1299)]
    elif service == "followers_guarantee":
        tiers = [(500, 189), (1000, 349), (5000, 1599)]
    else:
        return float(qty)

    for q, p in tiers:
        if qty == q:
            return float(p)

    tiers.sort(key=lambda x: x[0])

    if qty < tiers[0][0]:
        unit_rate = tiers[0][1] / tiers[0][0]
        return max(1.0, round(qty * unit_rate, 2))

    if qty > tiers[-1][0]:
        unit_rate = tiers[-1][1] / tiers[-1][0]
        return round(qty * unit_rate, 2)

    for i in range(len(tiers) - 1):
        q1, p1 = tiers[i]
        q2, p2 = tiers[i+1]
        if q1 < qty < q2:
            fraction = (qty - q1) / (q2 - q1)
            cost = p1 + fraction * (p2 - p1)
            return round(cost, 2)

    return round(qty * 0.1, 2)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data.clear()

    is_joined = await check_force_join(user.id, context)
    if not is_joined:
        await update.message.reply_text(
            f"⚠️ **Access Restricted!**\n\n"
            f"Welcome to **Aditya Services**!\n"
            f"Bot use karne ke liye pehle hamaara official channel join karein.\n\n"
            f"👉 Pehle channel join karein aur phir **✅ Verify / I Have Joined** button par click karein.",
            parse_mode="Markdown",
            reply_markup=get_force_join_keyboard()
        )
        return

    await update.message.reply_text(
        f"🚀 **Welcome to Aditya Services Bot!** 🚀\n\n"
        f"Your trusted platform for premium Instagram growth services.\n"
        f"Please select an option below to get started:",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "check_join":
        is_joined = await check_force_join(user_id, context)
        if is_joined:
            await query.edit_message_text(
                "✅ **Verification Successful!**\n\nWelcome to **Aditya Services**! Select a service to continue:",
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await query.answer("❌ Aapne channel join nahi kiya hai!", show_alert=True)
            await query.edit_message_text(
                "❌ **Verification Failed!**\nAapne abhi tak channel join nahi kiya hai. Niche button se join karke verify dabayein.",
                parse_mode="Markdown",
                reply_markup=get_force_join_keyboard()
            )
        return

    # Admin Approval Handler via Inline Button (LuvSMM API Call)
    if query.data.startswith("approve_"):
        if user_id != ADMIN_ID:
            await query.answer("❌ You are not authorized!", show_alert=True)
            return
        
        idx = int(query.data.replace("approve_", ""))
        orders = load_orders()
        
        if idx < len(orders):
            ord_data = orders[idx]
            service_key = ord_data.get("raw_service")
            service_id = SERVICE_IDS.get(service_key)
            link = ord_data.get("link")
            qty = ord_data.get("quantity")

            if not service_id:
                await query.answer("❌ Service ID mapping not found!", show_alert=True)
                return

            # LuvSMM API Request Payload
            payload = {
                'key': SMM_API_KEY,
                'action': 'add',
                'service': service_id,
                'link': link,
                'quantity': qty
            }

            try:
                response = requests.post(SMM_API_URL, data=payload).json()
                if "order" in response:
                    orders[idx]["status"] = "✅ Completed / Sent to SMM"
                    with open(ORDERS_FILE, "w") as f:
                        json.dump(orders, f, indent=4)
                    
                    smm_order_id = response.get("order")
                    await query.edit_message_caption(
                        caption=query.message.caption + f"\n\n🚀 **Status:** Approved & Sent to LuvSMM (Order ID: `{smm_order_id}`)",
                        parse_mode="Markdown"
                    )
                    await query.answer("✅ Order successfully placed on LuvSMM Panel!")
                else:
                    error_msg = response.get("error", "Unknown error")
                    await query.answer(f"❌ SMM Error: {error_msg}", show_alert=True)
            except Exception as e:
                await query.answer(f"❌ API Request Failed: {e}", show_alert=True)
        return

    is_joined = await check_force_join(user_id, context)
    if not is_joined:
        await query.edit_message_text(
            "⚠️ **Access Denied!**\nPlease join our official channel to continue using this bot.",
            parse_mode="Markdown",
            reply_markup=get_force_join_keyboard()
        )
        return

    if query.data == "my_orders":
        all_orders = load_orders()
        user_orders = [o for o in all_orders if o.get("user_id") == user_id]

        if not user_orders:
            msg = "📋 **My Orders**\n\nAapne abhi tak koi order nahi diya hai."
        else:
            msg = "📋 **Your Recent Orders:**\n\n"
            for idx, ord_data in enumerate(user_orders[-5:], 1):
                service_name = str(ord_data.get('service', '')).replace('_', ' ').title()
                msg += (
                    f"**{idx}. Service:** {service_name}\n"
                    f"   • **Quantity:** {ord_data.get('quantity')}\n"
                    f"   • **Cost:** ₹{ord_data.get('cost')}\n"
                    f"   • **Status:** {ord_data.get('status', 'Pending Verification')}\n"
                    f"   • **Link:** `{ord_data.get('link')}`\n\n"
                )

        back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu")]])
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=back_keyboard)
        return

    if query.data == "back_to_menu":
        await query.edit_message_text(
            "🚀 **Aditya Services — Main Menu**\nPlease select a service or check your orders:",
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard()
        )
        return

    if query.data.startswith("service_"):
        service_key = query.data.replace("service_", "")
        context.user_data["selected_service"] = service_key

        if service_key == "views":
            txt = (
                "👁️ **Instagram Reel Views**\n\n"
                "Select packages or enter any custom quantity:\n"
                "• 10000 views -> ₹19\n"
                "• 50000 views -> ₹49\n"
                "• 100000 views -> ₹79\n"
                "• 1000000 views -> ₹299 (Best Value)\n\n"
                "👉 **Send your desired Quantity:**"
            )
        elif service_key == "likes":
            txt = (
                "❤️ **Instagram Likes**\n\n"
                "Select packages or enter any custom quantity:\n"
                "• 1000 likes -> ₹20\n"
                "• 5000 likes -> ₹60\n"
                "• 10000 likes -> ₹110 (Best Value)\n\n"
                "👉 **Send your desired Quantity:**"
            )
        elif service_key == "comments":
            txt = (
                "💬 **Instagram Custom Comments**\n\n"
                "Select packages or enter any custom quantity:\n"
                "• 100 -> ₹29\n"
                "• 1000 -> ₹229\n"
                "• 2000 -> ₹399\n"
                "• 4000 -> ₹749\n"
                "• 6000 -> ₹1,099\n"
                "• 8000 -> ₹1,399\n"
                "• 10000 -> ₹1,699 (Best Value)\n\n"
                "👉 **Send your desired Quantity:**"
            )
        elif service_key == "followers_no_refill":
            txt = (
                "👥 **Instagram Followers (No Refill)**\n\n"
                "Select packages or enter any custom quantity:\n"
                "• 500 -> ₹149\n"
                "• 1000 -> ₹279\n"
                "• 5000 -> ₹1,299 (Best Value)\n\n"
                "👉 **Send your desired Quantity:**"
            )
        elif service_key == "followers_guarantee":
            txt = (
                "👥 **Instagram Followers (Lifetime Refill)**\n\n"
                "Select packages or enter any custom quantity:\n"
                "• 500 -> ₹189\n"
                "• 1000 -> ₹349\n"
                "• 5000 -> ₹1,599 (Best Value)\n\n"
                "👉 **Send your desired Quantity:**"
            )
        
        context.user_data["step"] = "awaiting_quantity"
        await query.edit_message_text(txt, parse_mode="Markdown")

    elif query.data == "contact_support":
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Chat with Admin Directly", url=SUPPORT_LINK)],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu")]
        ])
        await query.edit_message_text(
            f"📞 **Customer Support**\n\nFor any queries or order support, click below to chat with Admin directly:",
            parse_mode="Markdown",
            reply_markup=back_keyboard
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    is_joined = await check_force_join(user.id, context)
    if not is_joined:
        await update.message.reply_text(
            "⚠️ **Access Restricted!**\nPlease join our official channel first to use this bot.",
            parse_mode="Markdown",
            reply_markup=get_force_join_keyboard()
        )
        return

    text = update.message.text.strip()
    step = context.user_data.get("step")

    if step == "awaiting_quantity":
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text("❌ Please enter a valid numerical quantity.")
            return
        
        qty = int(text)
        service = context.user_data.get("selected_service")
        
        cost = calculate_cost(service, qty)

        if cost < 1:
            cost = 1.0

        context.user_data["quantity"] = qty
        context.user_data["cost"] = cost
        context.user_data["step"] = "awaiting_link"

        if "followers" in service:
            prompt = "🔗 Please send your **Instagram Profile Link** (e.g., `https://instagram.com/your_username`):"
        else:
            prompt = "🔗 Please send your **Instagram Reel/Post Link** (e.g., `https://instagram.com/reel/xyz...`):"

        await update.message.reply_text(f"💰 Total Amount: **₹{cost}**\n\n{prompt}", parse_mode="Markdown")

    elif step == "awaiting_link":
        if "instagram.com" not in text.lower():
            await update.message.reply_text("❌ Invalid Instagram link. Please send a valid `instagram.com` link.")
            return

        context.user_data["link"] = text
        cost = context.user_data["cost"]
        service = context.user_data.get("selected_service").replace("_", " ").title()
        qty = context.user_data["quantity"]

        upi_url = f"upi://pay?pa={UPI_ID}&pn=Aditya%20Services&am={cost}&cu=INR"
        qr_code_api = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_url)}"

        caption = (
            f"💳 **Aditya Services — Order Invoice**\n\n"
            f"📌 **Service:** {service}\n"
            f"📊 **Quantity:** {qty}\n"
            f"🔗 **Target Link:** `{text}`\n"
            f"💵 **Total Amount to Pay:** ₹{cost}\n\n"
            f"📌 **Instructions:**\n"
            f"1. Scan the QR code above using PhonePe / Google Pay / Paytm / FamPay.\n"
            f"2. Pay **₹{cost}**.\n"
            f"3. **Send the Payment Screenshot right here in this chat** as proof."
        )

        context.user_data["step"] = "awaiting_screenshot"
        await update.message.reply_photo(photo=qr_code_api, caption=caption, parse_mode="Markdown")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1].file_id

    raw_service = context.user_data.get("selected_service", "unknown_service")
    service_formatted = str(raw_service).replace('_', ' ').title()
    
    quantity = context.user_data.get("quantity", "N/A")
    cost = context.user_data.get("cost", "N/A")
    link = context.user_data.get("link", "N/A")

    order_info = {
        "user_id": user.id,
        "username": f"@{user.username}" if user.username else "No Username",
        "raw_service": raw_service,
        "service": service_formatted,
        "quantity": quantity,
        "cost": cost,
        "link": link,
        "status": "⏳ Pending Verification"
    }
    
    save_order(order_info)
    orders = load_orders()
    order_idx = len(orders) - 1

    admin_text = (
        f"🚨 **NEW PAYMENT RECEIVED!** 🚨\n\n"
        f"👤 **User:** {order_info['username']} (ID: `{user.id}`)\n"
        f"🛠️ **Service Type:** {order_info['service']}\n"
        f"📊 **Quantity:** {order_info['quantity']}\n"
        f"💵 **Amount Paid:** ₹{order_info['cost']}\n"
        f"🔗 **Target Link:** `{order_info['link']}`"
    )
    
    keyboard = [[InlineKeyboardButton("✅ Approve & Start Order", callback_data=f"approve_{order_idx}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_photo(
        chat_id=ADMIN_ID, 
        photo=photo, 
        caption=admin_text, 
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    await update.message.reply_text(
        "Thanks For Choosing Us , Your Order Will Be Completed Soon !\n\n"
        "Owner - @asoffcial",
        parse_mode="Markdown"
    )
    context.user_data.clear()

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("Usage: `/broadcast Your message here`", parse_mode="Markdown")
        return

    orders = load_orders()
    user_ids = list(set([o["user_id"] for o in orders if "user_id" in o]))

    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 **Aditya Services Announcement:**\n\n{msg}", parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(f"✅ **Broadcast Completed!**\n\nSent: {sent}\nFailed: {failed}")

def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    app_bot = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .build()
    )

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("broadcast", broadcast))
    app_bot.add_handler(CallbackQueryHandler(button_click))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🚀 Aditya Services Bot with LuvSMM API is Running on Render 24/7...")
    app_bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
            
