import telebot
from telebot import types
import requests
import random
import string
import json
import os
import time
import threading
from datetime import datetime
from faker import Faker
import gspread
from google.oauth2.service_account import Credentials

# ========================= CONFIG =========================
TOKEN = "7963114120:AAEQNSJqNqBGkDcxaTqZEtARYFQkNgyrmGg"
LOG_GROUP_ID = -1003925650198
ADMIN_ID = 5473188537

# Default Settings
EARNING_PER_ACCEPT = 10.0
SETTINGS_FILE = "settings.json"
USERS_FILE = "users.json"
PENDING_FILE = "pending.json" # নতুন ফাইল, অটো-এক্সেপ্টের জন্য

# ========================= UTILS & FILE LOADERS =========================
def load_settings():
    global EARNING_PER_ACCEPT
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                EARNING_PER_ACCEPT = data.get("price_per_account", 10.0)
        except:
            pass

def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump({"price_per_account": EARNING_PER_ACCEPT}, f, ensure_ascii=False, indent=2)

def load_json(filepath, default_type=dict):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return default_type()

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

load_settings()

# ========================= GOOGLE SHEET SETUP =========================
try:
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key("1Cet2bmuAfr1_92px80ai-QbEhKJKSGwdSHwAQZtIzS0")
    sheet = sh.worksheet("submit")
    print("✅ Google Sheet 'submit' Connected Successfully!")
except Exception as e:
    print("❌ Google Sheet Error:", e)
    sheet = None

bot = telebot.TeleBot(TOKEN)
fake = Faker()
user_states = {}

# ========================= CORE FUNCTIONS =========================
def generate_password():
    length = random.randint(10, 14)
    chars = string.ascii_letters + string.digits + "@#$&*"
    return ''.join(random.choice(chars) for _ in range(length))

def generate_account():
    first = fake.first_name()
    last = fake.last_name()
    username = f"{first.lower()}{last.lower()}{random.randint(100, 9999)}"
    email = f"{username}@hotmail.com"
    password = generate_password()
    return first, last, email, password

def check_email(email):
    available_text = "Neither"
    link = f"https://odc.officeapps.live.com/odc/emailhrd/getidp?hm=0&emailAddress={email}&_=1604288577990"
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Connection": "keep-alive",
        "Host": "odc.officeapps.live.com",
    }
    try:
        response = requests.get(link, headers=headers, timeout=12).text
        if available_text in response:
            return email
    except:
        pass
    return None

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🚀 Create Hotmail", "💰 My Balance")
    markup.add("📖 Tutorial", "💸 Withdraw")
    return markup

# ========================= SHARED ACCEPTANCE LOGIC =========================
def process_acceptance(req_id, req_data, action_by="Admin"):
    """
    এই ফাংশনটি অ্যাডমিন বা অটো-সিস্টেম উভয়ের জন্যই এক্সেপ্ট করার কাজ করবে।
    """
    user_chat_id = req_data["user_chat_id"]
    email = req_data["email"]
    password = req_data["password"]
    price = req_data.get("price", EARNING_PER_ACCEPT)
    admin_msg_id = req_data.get("admin_message_id")

    # 1. Update Google Sheet
    if sheet:
        try:
            sheet.append_row([email, password])
        except Exception as e:
            print("Sheet Append Error:", e)

    # 2. Update User Balance
    users = load_json(USERS_FILE)
    uid = str(user_chat_id)
    if uid not in users:
        users[uid] = {"balance": 0.0, "pending_balance": 0.0}
    
    # Deduct from pending, add to confirmed
    users[uid]["pending_balance"] = max(0.0, users[uid].get("pending_balance", 0.0) - price)
    users[uid]["balance"] = users[uid].get("balance", 0.0) + price
    save_json(USERS_FILE, users)

    # 3. Notify User
    success_msg = (
        f"🎉 <b>অভিনন্দন! অ্যাকাউন্ট ভেরিফায়েড।</b>\n\n"
        f"আপনার সাবমিট করা ইমেইল: <code>{email}</code> গ্রহণযোগ্য হয়েছে।\n"
        f"<b>+{price} টাকা</b> আপনার মেইন ব্যালেন্সে যোগ করা হয়েছে।\n\n"
        f"<i>অপ্রুভ করেছে: {action_by}</i>"
    )
    try:
        bot.send_message(user_chat_id, success_msg, parse_mode="HTML")
    except:
        pass # User might have blocked the bot

    # 4. Update Admin Message in Group
    if admin_msg_id:
        try:
            admin_text = (
                f"✅ <b>অ্যাকাউন্ট গ্রহণ করা হয়েছে</b>\n\n"
                f"Username : <code>{email}</code>\n"
                f"Password : <code>{password}</code>\n\n"
                f"👤 <b>Status:</b> Accepted by {action_by}"
            )
            bot.edit_message_text(admin_text, LOG_GROUP_ID, admin_msg_id, parse_mode="HTML")
        except:
            pass

    # 5. Remove from pending list
    pending_data = load_json(PENDING_FILE)
    if req_id in pending_data:
        del pending_data[req_id]
        save_json(PENDING_FILE, pending_data)


# ========================= BACKGROUND WORKER (AUTO-ACCEPT) =========================
def auto_accept_worker():
    """
    প্রতি ৫ মিনিট পর পর চেক করবে, যদি কোনো অ্যাকাউন্টের বয়স ২৪ ঘণ্টার বেশি হয়,
    তবে তা অটোমেটিক এক্সেপ্ট করে নিবে।
    """
    while True:
        try:
            pending_requests = load_json(PENDING_FILE)
            current_time = time.time()
            
            for req_id, data in list(pending_requests.items()):
                timestamp = data.get("timestamp", 0)
                # 86400 seconds = 24 Hours
                if (current_time - timestamp) >= 86400:
                    print(f"Auto-Accepting Request: {req_id}")
                    process_acceptance(req_id, data, action_by="Auto-System (24h)")
                    
        except Exception as e:
            print("Auto-Accept Worker Error:", e)
        
        time.sleep(300) # Check every 5 minutes

# Start the background thread
threading.Thread(target=auto_accept_worker, daemon=True).start()


# ========================= HANDLERS =========================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🌟 <b>স্বাগতম আমাদের প্রফেশনাল হটমেইল ক্রিয়েটর বটে!</b> 🌟\n\n"
        "এখানে আপনি খুব সহজেই Hotmail অ্যাকাউন্ট তৈরি করে টাকা ইনকাম করতে পারবেন। "
        "প্রতিটি সঠিক অ্যাকাউন্টের বিনিময়ে আমরা আপনাকে নির্দিষ্ট পরিমাণ টাকা পেমেন্ট করবো।\n\n"
        "<b>🔹 কাজের নিয়মাবলি:</b>\n"
        "• বট থেকে নাম ও পাসওয়ার্ড দেওয়া হবে।\n"
        "• সেই তথ্য দিয়ে আউটলুক/হটমেইলে অ্যাকাউন্ট খুলতে হবে।\n"
        "• সাবমিট করার পর তা আমাদের প্যানেলে রিভিউতে যাবে।\n"
        "• সবকিছু ঠিক থাকলে আপনার ব্যালেন্সে টাকা যোগ হবে।\n\n"
        "🚀 <i>শুরু করতে নিচের বাটনগুলো ব্যবহার করুন 👇</i>"
    )
    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )
    
    users = load_json(USERS_FILE)
    uid = str(message.chat.id)
    if uid not in users:
        users[uid] = {"balance": 0.0, "pending_balance": 0.0}
        save_json(USERS_FILE, users)

@bot.message_handler(commands=['setprice'])
def set_price(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        new_price = float(message.text.split()[1])
        global EARNING_PER_ACCEPT
        EARNING_PER_ACCEPT = new_price
        save_settings()
        bot.reply_to(message, f"✅ <b>সিস্টেম প্রাইস আপডেট করা হয়েছে!</b>\nবর্তমান প্রাইস: <b>{new_price} টাকা</b> প্রতি অ্যাকাউন্ট।", parse_mode="HTML")
    except:
        bot.reply_to(message, "⚠️ <b>সঠিক নিয়ম:</b> <code>/setprice 15</code>", parse_mode="HTML")

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    text = message.text.strip()
    chat_id = message.chat.id
    users = load_json(USERS_FILE)
    uid = str(chat_id)

    if text == "🚀 Create Hotmail":
        first, last, email, password = generate_account()
        user_states[chat_id] = {"first": first, "last": last, "email": email, "password": password}

        info = (
            f"📋 <b>নতুন কাজের বিবরণী</b>\n\n"
            f"দয়া করে নিচের তথ্যগুলো ব্যবহার করে একটি নতুন Hotmail অ্যাকাউন্ট তৈরি করুন।\n\n"
            f"👤 <b>নাম:</b> <code>{first}</code> <code>{last}</code>\n"
            f"📧 <b>ইমেইল:</b> <code>{email}</code>\n"
            f"🔑 <b>পাসওয়ার্ড:</b> <code>{password}</code>\n\n"
            f"💰 <i>এই অ্যাকাউন্টটি সঠিকভাবে তৈরি ও সাবমিট করলে আপনার ব্যালেন্সে <b>{EARNING_PER_ACCEPT} টাকা</b> যোগ হবে।</i>\n\n"
            f"⚠️ <b>সতর্কতা:</b> অ্যাকাউন্ট তৈরি সম্পূর্ণ হওয়ার পরেই কনফার্ম করবেন।"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ আমি তৈরি করেছি (ধাপ ১)", callback_data="confirm_step1"))
        bot.send_message(chat_id, info, parse_mode="HTML", reply_markup=markup)

    elif text == "💰 My Balance":
        confirmed = users.get(uid, {}).get("balance", 0.0)
        pending = users.get(uid, {}).get("pending_balance", 0.0)
        
        balance_text = (
            f"💼 <b>আপনার ফাইন্যান্সিয়াল স্ট্যাটাস</b>\n\n"
            f"💵 <b>মেইন ব্যালেন্স:</b> <code>{confirmed:.2f} ৳</code>\n"
            f"<i>(এই টাকা আপনি যেকোনো সময় উইথড্র করতে পারবেন)</i>\n\n"
            f"⏳ <b>পেন্ডিং ব্যালেন্স:</b> <code>{pending:.2f} ৳</code>\n"
            f"<i>(অ্যাকাউন্টগুলো রিভিউতে আছে। ২৪ ঘণ্টার মাঝে আপডেট হবে)</i>\n\n"
            f"📊 সর্বমোট আয়: <code>{(confirmed + pending):.2f} ৳</code>"
        )
        bot.send_message(chat_id, balance_text, parse_mode="HTML")

    elif text == "📖 Tutorial":
        tutorial_text = (
            "📖 <b>কাজের সম্পূর্ণ নির্দেশিকা:</b>\n\n"
            "<b>ধাপ ১:</b> <code>🚀 Create Hotmail</code> বাটনে ক্লিক করে কাজের তথ্য নিন।\n"
            "<b>ধাপ ২:</b> আপনার ব্রাউজারে outlook.com এ গিয়ে ওই নাম, ইমেইল এবং পাসওয়ার্ড দিয়ে নতুন একটি অ্যাকাউন্ট তৈরি করুন।\n"
            "<b>ধাপ ৩:</b> অ্যাকাউন্ট তৈরি সফলভাবে সম্পন্ন হলে, টেলিগ্রামে ফিরে এসে কনফার্মেশন বাটনে চাপ দিন।\n"
            "<b>ধাপ ৪:</b> আপনার সাবমিশনটি পেন্ডিংয়ে চলে যাবে। আমাদের এডমিন প্যানেল সেটি চেক করবে।\n"
            "<b>ধাপ ৫:</b> যদি এডমিন ২৪ ঘণ্টার মধ্যে চেক না করে, সিস্টেম <b>অটোমেটিক</b> আপনার ব্যালেন্সে টাকা যোগ করে দেবে।\n\n"
            "⚠️ <i>ভুল তথ্য দিয়ে কনফার্ম করলে পরবর্তীতে আপনার আইডি ব্যান হতে পারে।</i>"
        )
        bot.send_message(chat_id, tutorial_text, parse_mode="HTML")

    elif text == "💸 Withdraw":
        if uid not in users or users[uid].get("balance", 0.0) < 50:
            bot.send_message(chat_id, "⚠️ <b>উইথড্র বাতিল:</b> উইথড্র করার জন্য আপনার মেইন ব্যালেন্সে ন্যূনতম <b>৫০ টাকা</b> থাকতে হবে।", parse_mode="HTML")
            return

        bal = users[uid]["balance"]
        w_id = f"WD-{random.randint(100000000, 999999999)}"
        dt = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        name = message.from_user.first_name
        username = f"@{message.from_user.username}" if message.from_user.username else "No Username"

        invoice = (
            f"🧾 <b>অফিসিয়াল উইথড্র ইনভয়েস</b> 🧾\n\n"
            f"<b>ইনভয়েস আইডি:</b> <code>{w_id}</code>\n"
            f"<b>তারিখ ও সময়:</b> {dt}\n\n"
            f"👤 <b>নাম:</b> {name}\n"
            f"🆔 <b>ইউজার আইডি:</b> <code>{chat_id}</code>\n"
            f"🔗 <b>ইউজারনেম:</b> {username}\n"
            f"💵 <b>উইথড্র অ্যামাউন্ট:</b> <b>{bal:.2f} টাকা</b>\n\n"
            f"📌 <b>পরবর্তী করণীয়:</b>\n"
            f"এই মেসেজটি সম্পূর্ণ কপি বা ফরওয়ার্ড করে আমাদের পেমেন্ট বট <b>@otp_paybot</b> এ পাঠিয়ে দিন। খুব শীঘ্রই আপনার পেমেন্ট ক্লিয়ার করা হবে।"
        )

        # Zero out balance after withdrawal request
        users[uid]["balance"] = 0.0
        save_json(USERS_FILE, users)

        bot.send_message(chat_id, invoice, parse_mode="HTML")
        bot.send_message(chat_id, "✅ আপনার ইনভয়েস জেনারেট করা হয়েছে। অনুগ্রহ করে উপরের ইনভয়েসটি পেমেন্ট বটে পাঠান।")

# ========================= CALLBACKS =========================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "confirm_step1":
        if chat_id not in user_states:
            bot.answer_callback_query(call.id, "⚠️ সেশন এক্সপায়ার হয়ে গেছে! নতুন কাজ নিন।", show_alert=True)
            return
        
        acc = user_states[chat_id]
        bot.answer_callback_query(call.id, "✅ প্রথম ধাপ সম্পন্ন হয়েছে।")

        confirm2 = (
            f"🔄 <b>ফাইনাল কনফার্মেশন (ধাপ ২/২)</b>\n\n"
            f"অনুগ্রহ করে ডাটাগুলো আরেকবার মিলিয়ে নিন:\n"
            f"📧 <b>ইমেইল:</b> <code>{acc['email']}</code>\n"
            f"🔑 <b>পাসওয়ার্ড:</b> <code>{acc['password']}</code>\n\n"
            f"আপনি কি নিশ্চিত যে অ্যাকাউন্টটি পুরোপুরি প্রস্তুত এবং রিকভারি সেটআপ করা হয়নি?"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚀 হ্যাঁ, অ্যাকাউন্ট সম্পন্ন হয়েছে", callback_data="final_confirm"))
        bot.edit_message_text(confirm2, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

    elif data == "final_confirm":
        if chat_id not in user_states:
            bot.answer_callback_query(call.id, "⚠️ কোনো ডাটা পাওয়া যায়নি!", show_alert=True)
            return

        acc = user_states[chat_id]
        email = acc["email"]
        bot.answer_callback_query(call.id, "🔍 মাইক্রোসফট সার্ভারে চেক করা হচ্ছে...")
        bot.edit_message_text("⏳ <i>অ্যাকাউন্টের রিয়েল-টাইম স্ট্যাটাস যাচাই করা হচ্ছে, দয়া করে অপেক্ষা করুন...</i>", chat_id, call.message.message_id, parse_mode="HTML")

        # Microsoft system check
        is_available = check_email(email) is not None
        del user_states[chat_id]

        if is_available:
            bot.edit_message_text(f"❌ <b>অ্যাকাউন্ট বাতিল (Rejected)</b>\n\nআমাদের চেকার বলছে <code>{email}</code> অ্যাকাউন্টটি এখনো খোলা হয়নি। আপনি অ্যাকাউন্ট না খুলেই কনফার্ম করেছেন।", chat_id, call.message.message_id, parse_mode="HTML")
        else:
            request_id = f"req_{int(time.time())}_{random.randint(1000,9999)}"
            price = EARNING_PER_ACCEPT
            
            # Update user pending balance
            users = load_json(USERS_FILE)
            uid = str(chat_id)
            if uid not in users:
                users[uid] = {"balance": 0.0, "pending_balance": 0.0}
            users[uid]["pending_balance"] = users[uid].get("pending_balance", 0.0) + price
            save_json(USERS_FILE, users)

            # Inform User
            bot.edit_message_text(
                f"✅ <b>অ্যাকাউন্টটি সাবমিট হয়েছে!</b>\n\n"
                f"আপনার অ্যাকাউন্টটি আমাদের রিভিউ প্যানেলে পাঠানো হয়েছে।\n"
                f"<b>{price} টাকা</b> আপনার <b>পেন্ডিং ব্যালেন্সে</b> যোগ করা হয়েছে।\n\n"
                f"⏱ <i>অ্যাডমিন চেক করার পর ব্যালেন্স কনফার্ম হবে। যদি ২৪ ঘণ্টার মাঝে অ্যাডমিন চেক না করে, সিস্টেম অটোমেটিক টাকা মেইন ব্যালেন্সে যোগ করে দিবে।</i>",
                chat_id, call.message.message_id, parse_mode="HTML"
            )

            # Send to Admin Group
            log_text = (
                f"🔔 <b>নতুন অ্যাকাউন্ট রিভিউ রিকোয়েস্ট</b>\n\n"
                f"👤 <b>Worker Name:</b> {acc['first']} {acc['last']}\n"
                f"🆔 <b>Worker ID:</b> <code>{chat_id}</code>\n\n"
                f"📧 <b>Email:</b> <code>{email}</code>\n"
                f"🔑 <b>Password:</b> <code>{acc['password']}</code>\n"
                f"💰 <b>Cost:</b> {price} BDT\n\n"
                f"<i>(Note: This will auto-accept in 24 hours if ignored)</i>"
            )

            log_markup = types.InlineKeyboardMarkup(row_width=2)
            log_markup.add(
                types.InlineKeyboardButton("✅ এক্সেপ্ট (কিনবো)", callback_data=f"accept:{request_id}"),
                types.InlineKeyboardButton("❌ রিজেক্ট (বাদ)", callback_data=f"reject:{request_id}")
            )
            
            admin_msg = bot.send_message(LOG_GROUP_ID, log_text, parse_mode="HTML", reply_markup=log_markup)

            # Save to persistent pending JSON file
            pending_requests = load_json(PENDING_FILE)
            pending_requests[request_id] = {
                "user_chat_id": chat_id,
                "first": acc["first"],
                "last": acc["last"],
                "email": email,
                "password": acc["password"],
                "price": price,
                "timestamp": time.time(),
                "admin_message_id": admin_msg.message_id # To edit the message later via Auto-accept
            }
            save_json(PENDING_FILE, pending_requests)


    elif data.startswith("accept:") or data.startswith("reject:"):
        action, req_id = data.split(":", 1)
        pending_requests = load_json(PENDING_FILE)
        
        if req_id not in pending_requests:
            bot.answer_callback_query(call.id, "⚠️ এই রিকোয়েস্টটি আগেই প্রসেস করা হয়েছে বা অটো-এক্সেপ্ট হয়ে গেছে!", show_alert=True)
            bot.edit_message_text(call.message.text + "\n\n🔒 <i>Already Processed</i>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            return

        req_data = pending_requests[req_id]
        user_chat_id = req_data["user_chat_id"]
        price = req_data.get("price", EARNING_PER_ACCEPT)

        if action == "accept":
            bot.answer_callback_query(call.id, "অ্যাকাউন্টটি গ্রহণ করা হয়েছে।")
            # Call shared logic
            process_acceptance(req_id, req_data, action_by="Admin")
            
        else:  # Reject Action
            bot.answer_callback_query(call.id, "অ্যাকাউন্টটি বাতিল করা হয়েছে।")
            users = load_json(USERS_FILE)
            uid = str(user_chat_id)

            # Deduct from pending balance
            if uid in users:
                users[uid]["pending_balance"] = max(0.0, users[uid].get("pending_balance", 0.0) - price)
                save_json(USERS_FILE, users)

            # Notify User
            reject_msg = (
                f"❌ <b>অ্যাকাউন্ট বাতিল করা হয়েছে</b>\n\n"
                f"আপনার দেওয়া <code>{req_data['email']}</code> অ্যাকাউন্টটিতে সমস্যা পাওয়ায় অ্যাডমিন তা বাতিল করেছেন।\n"
                f"দয়া করে পরবর্তী অ্যাকাউন্টগুলো সতর্কতার সাথে তৈরি করুন।"
            )
            try:
                bot.send_message(user_chat_id, reject_msg, parse_mode="HTML")
            except: pass

            # Update Admin Message
            try:
                bot.edit_message_text(call.message.text + "\n\n❌ <b>Status:</b> Rejected by Admin", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            except: pass

            # Remove from pending list
            del pending_requests[req_id]
            save_json(PENDING_FILE, pending_requests)


if __name__ == "__main__":
    print("========================================")
    print("🚀 Professional Hotmail Creator Bot Running...")
    print(f"💰 Current Price: {EARNING_PER_ACCEPT} BDT")
    print(f"⏱ Auto-Accept Worker: Active (24 Hours cycle)")
    print("========================================")
    bot.infinity_polling(timeout=20, long_polling_timeout=15)