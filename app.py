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
PENDING_FILE = "pending.json"

# ========================= TRANSLATIONS =========================
TEXTS = {
    "en": {
        "btn_create": "🚀 Create Hotmail",
        "btn_balance": "💰 My Balance",
        "btn_tutorial": "📖 Tutorial",
        "btn_withdraw": "💸 Withdraw",
        "choose_lang": "🌐 Please select your language:\nঅনুগ্রহ করে আপনার ভাষা নির্বাচন করুন:",
        "welcome": "🌟 <b>Welcome to our Professional Hotmail Creator Bot!</b> 🌟\n\nEarn money by creating Hotmail accounts easily. We pay a specific amount for each valid account.\n\n<b>🔹 Rules:</b>\n• The bot will provide a Name and Password.\n• Create an account on outlook.com/hotmail using that data.\n• Submit it, and it will go for review.\n• Once approved, money will be added to your balance.\n\n🚀 <i>Use the buttons below to start 👇</i>",
        "new_job": "📋 <b>New Task Details</b>\n\nPlease create a new Hotmail account using the details below.\n\n👤 <b>Name:</b> <code>{first}</code> <code>{last}</code>\n📧 <b>Email:</b> <code>{email}</code>\n🔑 <b>Password:</b> <code>{password}</code>\n\n💰 <i>You will get <b>{price} BDT</b> for successfully creating and submitting this account.</i>\n\n⚠️ <b>Warning:</b> Confirm only AFTER creating the account.",
        "confirm_btn1": "✅ I created it (Step 1)",
        "balance": "💼 <b>Your Financial Status</b>\n\n💵 <b>Main Balance:</b> <code>{confirmed:.2f} ৳</code>\n<i>(You can withdraw this anytime)</i>\n\n⏳ <b>Pending Balance:</b> <code>{pending:.2f} ৳</code>\n<i>(Accounts under review. Will be updated within 24h)</i>\n\n📊 Total Earnings: <code>{total:.2f} ৳</code>",
        "change_lang_btn": "🌐 Change Language",
        "tutorial": "📖 <b>Complete Guideline:</b>\n\n<b>Step 1:</b> Click <code>🚀 Create Hotmail</code> to get job details.\n<b>Step 2:</b> Go to outlook.com and create an account with the provided details.\n<b>Step 3:</b> After successful creation, come back here and confirm.\n<b>Step 4:</b> Your submission goes to pending. Our admin panel will review it.\n<b>Step 5:</b> If admin doesn't review within 24h, system will <b>automatically</b> add money to your balance.\n\n⚠️ <i>Submitting fake accounts may result in a ban.</i>",
        "withdraw_err": "⚠️ <b>Withdrawal Failed:</b> You need a minimum of <b>50 BDT</b> in your Main Balance to withdraw.",
        "invoice": "🧾 <b>Official Withdrawal Invoice</b> 🧾\n\n<b>Invoice ID:</b> <code>{w_id}</code>\n<b>Date & Time:</b> {dt}\n\n👤 <b>Name:</b> {name}\n🆔 <b>User ID:</b> <code>{chat_id}</code>\n🔗 <b>Username:</b> {username}\n💵 <b>Withdraw Amount:</b> <b>{bal:.2f} BDT</b>\n\n📌 <b>Next Step:</b>\nCopy or forward this complete message to our payment bot <b>@otp_paybot</b>. Your payment will be cleared very soon.",
        "invoice_gen": "✅ Your invoice has been generated. Please send the invoice above to the payment bot.",
        "session_exp": "⚠️ Session expired! Take a new job.",
        "step1_done": "✅ Step 1 completed.",
        "confirm_step2": "🔄 <b>Final Confirmation (Step 2/2)</b>\n\nPlease double check the details:\n📧 <b>Email:</b> <code>{email}</code>\n🔑 <b>Password:</b> <code>{password}</code>\n\nAre you sure the account is fully ready and no recovery was added?",
        "confirm_btn2": "🚀 Yes, account is ready",
        "no_data": "⚠️ No data found!",
        "checking": "🔍 Checking Microsoft servers...",
        "checking_msg": "⏳ <i>Verifying account real-time status, please wait...</i>",
        "rejected": "❌ <b>Account Rejected</b>\n\nOur checker says <code>{email}</code> hasn't been created yet. You confirmed without creating it.",
        "submitted": "✅ <b>Account Submitted!</b>\n\nYour account has been sent to our review panel.\n<b>{price} BDT</b> has been added to your <b>Pending Balance</b>.\n\n⏱ <i>Balance will be confirmed after admin check. If not checked in 24h, system will automatically approve it.</i>",
        "already_processed": "⚠️ This request was already processed or auto-accepted!",
        "accepted_alert": "Account accepted.",
        "rejected_alert": "Account rejected.",
        "success_msg": "🎉 <b>Congratulations! Account Verified.</b>\n\nYour submitted email: <code>{email}</code> is accepted.\n<b>+{price} BDT</b> added to your Main Balance.\n\n<i>Approved by: {action_by}</i>",
        "reject_msg": "❌ <b>Account Rejected</b>\n\nAdmin found issues with your submitted account <code>{email}</code> and rejected it.\nPlease be careful next time."
    },
    "bn": {
        "btn_create": "🚀 নতুন হটমেইল",
        "btn_balance": "💰 আমার ব্যালেন্স",
        "btn_tutorial": "📖 কাজের নিয়মাবলি",
        "btn_withdraw": "💸 টাকা উত্তোলন",
        "choose_lang": "🌐 Please select your language:\nঅনুগ্রহ করে আপনার ভাষা নির্বাচন করুন:",
        "welcome": "🌟 <b>স্বাগতম আমাদের প্রফেশনাল হটমেইল ক্রিয়েটর বটে!</b> 🌟\n\nএখানে আপনি খুব সহজেই Hotmail অ্যাকাউন্ট তৈরি করে টাকা ইনকাম করতে পারবেন। প্রতিটি সঠিক অ্যাকাউন্টের বিনিময়ে আমরা নির্দিষ্ট পরিমাণ টাকা পেমেন্ট করবো।\n\n<b>🔹 কাজের নিয়মাবলি:</b>\n• বট থেকে নাম ও পাসওয়ার্ড দেওয়া হবে।\n• সেই তথ্য দিয়ে আউটলুক/হটমেইলে অ্যাকাউন্ট খুলতে হবে।\n• সাবমিট করার পর তা আমাদের প্যানেলে রিভিউতে যাবে।\n• সবকিছু ঠিক থাকলে আপনার ব্যালেন্সে টাকা যোগ হবে।\n\n🚀 <i>শুরু করতে নিচের বাটনগুলো ব্যবহার করুন 👇</i>",
        "new_job": "📋 <b>নতুন কাজের বিবরণী</b>\n\nদয়া করে নিচের তথ্যগুলো ব্যবহার করে একটি নতুন Hotmail অ্যাকাউন্ট তৈরি করুন।\n\n👤 <b>নাম:</b> <code>{first}</code> <code>{last}</code>\n📧 <b>ইমেইল:</b> <code>{email}</code>\n🔑 <b>পাসওয়ার্ড:</b> <code>{password}</code>\n\n💰 <i>এই অ্যাকাউন্টটি সঠিকভাবে তৈরি ও সাবমিট করলে আপনার ব্যালেন্সে <b>{price} টাকা</b> যোগ হবে।</i>\n\n⚠️ <b>সতর্কতা:</b> অ্যাকাউন্ট তৈরি সম্পূর্ণ হওয়ার পরেই কনফার্ম করবেন।",
        "confirm_btn1": "✅ আমি তৈরি করেছি (ধাপ ১)",
        "balance": "💼 <b>আপনার ফাইন্যান্সিয়াল স্ট্যাটাস</b>\n\n💵 <b>মেইন ব্যালেন্স:</b> <code>{confirmed:.2f} ৳</code>\n<i>(এই টাকা আপনি যেকোনো সময় উইথড্র করতে পারবেন)</i>\n\n⏳ <b>পেন্ডিং ব্যালেন্স:</b> <code>{pending:.2f} ৳</code>\n<i>(অ্যাকাউন্টগুলো রিভিউতে আছে। ২৪ ঘণ্টার মাঝে আপডেট হবে)</i>\n\n📊 সর্বমোট আয়: <code>{total:.2f} ৳</code>",
        "change_lang_btn": "🌐 ভাষা পরিবর্তন (Language)",
        "tutorial": "📖 <b>কাজের সম্পূর্ণ নির্দেশিকা:</b>\n\n<b>ধাপ ১:</b> <code>🚀 নতুন হটমেইল</code> বাটনে ক্লিক করে কাজের তথ্য নিন।\n<b>ধাপ ২:</b> আপনার ব্রাউজারে outlook.com এ গিয়ে ওই নাম, ইমেইল এবং পাসওয়ার্ড দিয়ে নতুন একটি অ্যাকাউন্ট তৈরি করুন।\n<b>ধাপ ৩:</b> অ্যাকাউন্ট তৈরি সফলভাবে সম্পন্ন হলে, টেলিগ্রামে ফিরে এসে কনফার্মেশন বাটনে চাপ দিন।\n<b>ধাপ ৪:</b> আপনার সাবমিশনটি পেন্ডিংয়ে চলে যাবে। আমাদের এডমিন প্যানেল সেটি চেক করবে।\n<b>ধাপ ৫:</b> যদি এডমিন ২৪ ঘণ্টার মধ্যে চেক না করে, সিস্টেম <b>অটোমেটিক</b> আপনার ব্যালেন্সে টাকা যোগ করে দেবে।\n\n⚠️ <i>ভুল তথ্য দিয়ে কনফার্ম করলে পরবর্তীতে আপনার আইডি ব্যান হতে পারে।</i>",
        "withdraw_err": "⚠️ <b>উইথড্র বাতিল:</b> উইথড্র করার জন্য আপনার মেইন ব্যালেন্সে ন্যূনতম <b>৫০ টাকা</b> থাকতে হবে।",
        "invoice": "🧾 <b>অফিসিয়াল উইথড্র ইনভয়েস</b> 🧾\n\n<b>ইনভয়েস আইডি:</b> <code>{w_id}</code>\n<b>তারিখ ও সময়:</b> {dt}\n\n👤 <b>নাম:</b> {name}\n🆔 <b>ইউজার আইডি:</b> <code>{chat_id}</code>\n🔗 <b>ইউজারনেম:</b> {username}\n💵 <b>উইথড্র অ্যামাউন্ট:</b> <b>{bal:.2f} টাকা</b>\n\n📌 <b>পরবর্তী করণীয়:</b>\nএই মেসেজটি সম্পূর্ণ কপি বা ফরওয়ার্ড করে আমাদের পেমেন্ট বট <b>@otp_paybot</b> এ পাঠিয়ে দিন। খুব শীঘ্রই আপনার পেমেন্ট ক্লিয়ার করা হবে।",
        "invoice_gen": "✅ আপনার ইনভয়েস জেনারেট করা হয়েছে। অনুগ্রহ করে উপরের ইনভয়েসটি পেমেন্ট বটে পাঠান।",
        "session_exp": "⚠️ সেশন এক্সপায়ার হয়ে গেছে! নতুন কাজ নিন।",
        "step1_done": "✅ প্রথম ধাপ সম্পন্ন হয়েছে।",
        "confirm_step2": "🔄 <b>ফাইনাল কনফার্মেশন (ধাপ ২/২)</b>\n\nঅনুগ্রহ করে ডাটাগুলো আরেকবার মিলিয়ে নিন:\n📧 <b>ইমেইল:</b> <code>{email}</code>\n🔑 <b>পাসওয়ার্ড:</b> <code>{password}</code>\n\nআপনি কি নিশ্চিত যে অ্যাকাউন্টটি পুরোপুরি প্রস্তুত এবং রিকভারি সেটআপ করা হয়নি?",
        "confirm_btn2": "🚀 হ্যাঁ, অ্যাকাউন্ট সম্পন্ন হয়েছে",
        "no_data": "⚠️ কোনো ডাটা পাওয়া যায়নি!",
        "checking": "🔍 মাইক্রোসফট সার্ভারে চেক করা হচ্ছে...",
        "checking_msg": "⏳ <i>অ্যাকাউন্টের রিয়েল-টাইম স্ট্যাটাস যাচাই করা হচ্ছে, দয়া করে অপেক্ষা করুন...</i>",
        "rejected": "❌ <b>অ্যাকাউন্ট বাতিল (Rejected)</b>\n\nআমাদের চেকার বলছে <code>{email}</code> অ্যাকাউন্টটি এখনো খোলা হয়নি। আপনি অ্যাকাউন্ট না খুলেই কনফার্ম করেছেন।",
        "submitted": "✅ <b>অ্যাকাউন্টটি সাবমিট হয়েছে!</b>\n\nআপনার অ্যাকাউন্টটি আমাদের রিভিউ প্যানেলে পাঠানো হয়েছে।\n<b>{price} টাকা</b> আপনার <b>পেন্ডিং ব্যালেন্সে</b> যোগ করা হয়েছে।\n\n⏱ <i>অ্যাডমিন চেক করার পর ব্যালেন্স কনফার্ম হবে। যদি ২৪ ঘণ্টার মাঝে অ্যাডমিন চেক না করে, সিস্টেম অটোমেটিক টাকা মেইন ব্যালেন্সে যোগ করে দিবে।</i>",
        "already_processed": "⚠️ এই রিকোয়েস্টটি আগেই প্রসেস করা হয়েছে বা অটো-এক্সেপ্ট হয়ে গেছে!",
        "accepted_alert": "অ্যাকাউন্টটি গ্রহণ করা হয়েছে।",
        "rejected_alert": "অ্যাকাউন্টটি বাতিল করা হয়েছে।",
        "success_msg": "🎉 <b>অভিনন্দন! অ্যাকাউন্ট ভেরিফায়েড।</b>\n\nআপনার সাবমিট করা ইমেইল: <code>{email}</code> গ্রহণযোগ্য হয়েছে।\n<b>+{price} টাকা</b> আপনার মেইন ব্যালেন্সে যোগ করা হয়েছে।\n\n<i>অপ্রুভ করেছে: {action_by}</i>",
        "reject_msg": "❌ <b>অ্যাকাউন্ট বাতিল করা হয়েছে</b>\n\nআপনার দেওয়া <code>{email}</code> অ্যাকাউন্টটিতে সমস্যা পাওয়ায় অ্যাডমিন তা বাতিল করেছেন।\nদয়া করে পরবর্তী অ্যাকাউন্টগুলো সতর্কতার সাথে তৈরি করুন।"
    }
}

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

def get_user_lang(chat_id):
    users = load_json(USERS_FILE)
    return users.get(str(chat_id), {}).get("lang", "bn")  # Default to Bangla

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
    # Generate 6-8 random letters + current day (e.g., YsfjIK09)
    length = random.randint(6, 8)
    chars = string.ascii_letters
    random_str = ''.join(random.choice(chars) for _ in range(length))
    today_date = datetime.now().strftime("%d")
    return f"{random_str}{today_date}"

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

def get_main_keyboard(lang="bn"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(TEXTS[lang]["btn_create"], TEXTS[lang]["btn_balance"])
    markup.add(TEXTS[lang]["btn_tutorial"], TEXTS[lang]["btn_withdraw"])
    return markup

def get_lang_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇬🇧 English", callback_data="setlang_en"),
        types.InlineKeyboardButton("🇧🇩 বাংলা", callback_data="setlang_bn")
    )
    return markup

# ========================= SHARED ACCEPTANCE LOGIC =========================
def process_acceptance(req_id, req_data, action_by="Admin"):
    user_chat_id = req_data["user_chat_id"]
    email = req_data["email"]
    password = req_data["password"]
    price = req_data.get("price", EARNING_PER_ACCEPT)
    admin_msg_id = req_data.get("admin_message_id")

    if sheet:
        try:
            sheet.append_row([email, password])
        except Exception as e:
            print("Sheet Append Error:", e)

    users = load_json(USERS_FILE)
    uid = str(user_chat_id)
    if uid not in users:
        users[uid] = {"balance": 0.0, "pending_balance": 0.0, "lang": "bn"}
    
    users[uid]["pending_balance"] = max(0.0, users[uid].get("pending_balance", 0.0) - price)
    users[uid]["balance"] = users[uid].get("balance", 0.0) + price
    save_json(USERS_FILE, users)

    lang = users[uid].get("lang", "bn")
    success_msg = TEXTS[lang]["success_msg"].format(email=email, price=price, action_by=action_by)
    try:
        bot.send_message(user_chat_id, success_msg, parse_mode="HTML")
    except:
        pass

    if admin_msg_id:
        try:
            admin_text = (
                f"✅ <b>Account Accepted</b>\n\n"
                f"Username : <code>{email}</code>\n"
                f"Password : <code>{password}</code>\n\n"
                f"👤 <b>Status:</b> Accepted by {action_by}"
            )
            bot.edit_message_text(admin_text, LOG_GROUP_ID, admin_msg_id, parse_mode="HTML")
        except:
            pass

    pending_data = load_json(PENDING_FILE)
    if req_id in pending_data:
        del pending_data[req_id]
        save_json(PENDING_FILE, pending_data)

# ========================= BACKGROUND WORKER (AUTO-ACCEPT) =========================
def auto_accept_worker():
    while True:
        try:
            pending_requests = load_json(PENDING_FILE)
            current_time = time.time()
            
            for req_id, data in list(pending_requests.items()):
                timestamp = data.get("timestamp", 0)
                if (current_time - timestamp) >= 86400:
                    print(f"Auto-Accepting Request: {req_id}")
                    process_acceptance(req_id, data, action_by="Auto-System (24h)")
        except Exception as e:
            print("Auto-Accept Worker Error:", e)
        time.sleep(300)

threading.Thread(target=auto_accept_worker, daemon=True).start()

# ========================= HANDLERS =========================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    users = load_json(USERS_FILE)
    uid = str(chat_id)
    if uid not in users:
        users[uid] = {"balance": 0.0, "pending_balance": 0.0, "lang": "bn"}
        save_json(USERS_FILE, users)

    bot.send_message(chat_id, TEXTS["en"]["choose_lang"], reply_markup=get_lang_keyboard())

@bot.message_handler(commands=['setprice'])
def set_price(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        new_price = float(message.text.split()[1])
        global EARNING_PER_ACCEPT
        EARNING_PER_ACCEPT = new_price
        save_settings()
        bot.reply_to(message, f"✅ <b>System price updated!</b>\nCurrent Price: <b>{new_price} BDT</b> per account.", parse_mode="HTML")
    except:
        bot.reply_to(message, "⚠️ <b>Usage:</b> <code>/setprice 15</code>", parse_mode="HTML")

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    text = message.text.strip()
    chat_id = message.chat.id
    users = load_json(USERS_FILE)
    uid = str(chat_id)
    lang = get_user_lang(chat_id)

    if text in [TEXTS["en"]["btn_create"], TEXTS["bn"]["btn_create"]]:
        first, last, email, password = generate_account()
        user_states[chat_id] = {"first": first, "last": last, "email": email, "password": password}

        info = TEXTS[lang]["new_job"].format(first=first, last=last, email=email, password=password, price=EARNING_PER_ACCEPT)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(TEXTS[lang]["confirm_btn1"], callback_data="confirm_step1"))
        bot.send_message(chat_id, info, parse_mode="HTML", reply_markup=markup)

    elif text in [TEXTS["en"]["btn_balance"], TEXTS["bn"]["btn_balance"]]:
        confirmed = users.get(uid, {}).get("balance", 0.0)
        pending = users.get(uid, {}).get("pending_balance", 0.0)
        total = confirmed + pending
        
        balance_text = TEXTS[lang]["balance"].format(confirmed=confirmed, pending=pending, total=total)
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(TEXTS[lang]["change_lang_btn"], callback_data="choose_lang_again"))
        bot.send_message(chat_id, balance_text, parse_mode="HTML", reply_markup=markup)

    elif text in [TEXTS["en"]["btn_tutorial"], TEXTS["bn"]["btn_tutorial"]]:
        bot.send_message(chat_id, TEXTS[lang]["tutorial"], parse_mode="HTML")

    elif text in [TEXTS["en"]["btn_withdraw"], TEXTS["bn"]["btn_withdraw"]]:
        if uid not in users or users[uid].get("balance", 0.0) < 50:
            bot.send_message(chat_id, TEXTS[lang]["withdraw_err"], parse_mode="HTML")
            return

        bal = users[uid]["balance"]
        w_id = f"WD-{random.randint(100000000, 999999999)}"
        dt = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        name = message.from_user.first_name
        username = f"@{message.from_user.username}" if message.from_user.username else "No Username"

        invoice = TEXTS[lang]["invoice"].format(w_id=w_id, dt=dt, name=name, chat_id=chat_id, username=username, bal=bal)

        users[uid]["balance"] = 0.0
        save_json(USERS_FILE, users)

        bot.send_message(chat_id, invoice, parse_mode="HTML")
        bot.send_message(chat_id, TEXTS[lang]["invoice_gen"])

# ========================= CALLBACKS =========================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data
    lang = get_user_lang(chat_id)

    if data.startswith("setlang_"):
        new_lang = data.split("_")[1]
        users = load_json(USERS_FILE)
        uid = str(chat_id)
        if uid not in users:
            users[uid] = {"balance": 0.0, "pending_balance": 0.0}
        users[uid]["lang"] = new_lang
        save_json(USERS_FILE, users)
        
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, TEXTS[new_lang]["welcome"], parse_mode="HTML", reply_markup=get_main_keyboard(new_lang))

    elif data == "choose_lang_again":
        bot.edit_message_text(TEXTS[lang]["choose_lang"], chat_id, call.message.message_id, reply_markup=get_lang_keyboard())

    elif data == "confirm_step1":
        if chat_id not in user_states:
            bot.answer_callback_query(call.id, TEXTS[lang]["session_exp"], show_alert=True)
            return
        
        acc = user_states[chat_id]
        bot.answer_callback_query(call.id, TEXTS[lang]["step1_done"])

        confirm2 = TEXTS[lang]["confirm_step2"].format(email=acc['email'], password=acc['password'])
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(TEXTS[lang]["confirm_btn2"], callback_data="final_confirm"))
        bot.edit_message_text(confirm2, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

    elif data == "final_confirm":
        if chat_id not in user_states:
            bot.answer_callback_query(call.id, TEXTS[lang]["no_data"], show_alert=True)
            return

        acc = user_states[chat_id]
        email = acc["email"]
        bot.answer_callback_query(call.id, TEXTS[lang]["checking"])
        bot.edit_message_text(TEXTS[lang]["checking_msg"], chat_id, call.message.message_id, parse_mode="HTML")

        is_available = check_email(email) is not None
        del user_states[chat_id]

        if is_available:
            bot.edit_message_text(TEXTS[lang]["rejected"].format(email=email), chat_id, call.message.message_id, parse_mode="HTML")
        else:
            request_id = f"req_{int(time.time())}_{random.randint(1000,9999)}"
            price = EARNING_PER_ACCEPT
            
            users = load_json(USERS_FILE)
            uid = str(chat_id)
            if uid not in users:
                users[uid] = {"balance": 0.0, "pending_balance": 0.0, "lang": lang}
            users[uid]["pending_balance"] = users[uid].get("pending_balance", 0.0) + price
            save_json(USERS_FILE, users)

            bot.edit_message_text(TEXTS[lang]["submitted"].format(price=price), chat_id, call.message.message_id, parse_mode="HTML")

            log_text = (
                f"🔔 <b>New Account Review Request</b>\n\n"
                f"👤 <b>Worker Name:</b> {acc['first']} {acc['last']}\n"
                f"🆔 <b>Worker ID:</b> <code>{chat_id}</code>\n\n"
                f"📧 <b>Email:</b> <code>{email}</code>\n"
                f"🔑 <b>Password:</b> <code>{acc['password']}</code>\n"
                f"💰 <b>Cost:</b> {price} BDT\n\n"
                f"<i>(Note: This will auto-accept in 24 hours if ignored)</i>"
            )

            log_markup = types.InlineKeyboardMarkup(row_width=2)
            log_markup.add(
                types.InlineKeyboardButton("✅ Accept", callback_data=f"accept:{request_id}"),
                types.InlineKeyboardButton("❌ Reject", callback_data=f"reject:{request_id}")
            )
            admin_msg = bot.send_message(LOG_GROUP_ID, log_text, parse_mode="HTML", reply_markup=log_markup)

            pending_requests = load_json(PENDING_FILE)
            pending_requests[request_id] = {
                "user_chat_id": chat_id,
                "first": acc["first"],
                "last": acc["last"],
                "email": email,
                "password": acc["password"],
                "price": price,
                "timestamp": time.time(),
                "admin_message_id": admin_msg.message_id
            }
            save_json(PENDING_FILE, pending_requests)

    elif data.startswith("accept:") or data.startswith("reject:"):
        action, req_id = data.split(":", 1)
        pending_requests = load_json(PENDING_FILE)
        
        if req_id not in pending_requests:
            bot.answer_callback_query(call.id, TEXTS[lang]["already_processed"], show_alert=True)
            bot.edit_message_text(call.message.text + "\n\n🔒 <i>Already Processed</i>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            return

        req_data = pending_requests[req_id]
        user_chat_id = req_data["user_chat_id"]
        price = req_data.get("price", EARNING_PER_ACCEPT)

        if action == "accept":
            bot.answer_callback_query(call.id, TEXTS[lang]["accepted_alert"])
            process_acceptance(req_id, req_data, action_by="Admin")
            
        else:
            bot.answer_callback_query(call.id, TEXTS[lang]["rejected_alert"])
            users = load_json(USERS_FILE)
            uid = str(user_chat_id)
            target_lang = users.get(uid, {}).get("lang", "bn")

            if uid in users:
                users[uid]["pending_balance"] = max(0.0, users[uid].get("pending_balance", 0.0) - price)
                save_json(USERS_FILE, users)

            reject_msg = TEXTS[target_lang]["reject_msg"].format(email=req_data['email'])
            try:
                bot.send_message(user_chat_id, reject_msg, parse_mode="HTML")
            except: pass

            try:
                bot.edit_message_text(call.message.text + "\n\n❌ <b>Status:</b> Rejected by Admin", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            except: pass

            del pending_requests[req_id]
            save_json(PENDING_FILE, pending_requests)

if __name__ == "__main__":
    print("========================================")
    print("🚀 Professional Hotmail Creator Bot Running...")
    print(f"💰 Current Price: {EARNING_PER_ACCEPT} BDT")
    print(f"⏱ Auto-Accept Worker: Active (24 Hours cycle)")
    print("========================================")
    bot.infinity_polling(timeout=20, long_polling_timeout=15)
