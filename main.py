import os
import sys
import json
import asyncio
import threading
import logging
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from firebase_admin import credentials, firestore, initialize_app
from dotenv import load_dotenv

# Load environment variables (for local testing)
load_dotenv()

# --- CONFIGURATION ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# --- LOGGING SETUP ---
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FLASK SETUP (For Keep-Alive on Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running..."

def run_flask():
    # Render assigns the port via the PORT environment variable (default 10000 or 8080)
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- FIREBASE SETUP (Modified for Render) ---
# We check for the Environment Variable first (Deployment mode)
firebase_env = os.getenv("FIREBASE_SERVICE_ACCOUNT")

if firebase_env:
    try:
        # Parse the JSON string from the Environment Variable
        cred_dict = json.loads(firebase_env)
        cred = credentials.Certificate(cred_dict)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing FIREBASE_SERVICE_ACCOUNT JSON: {e}")
        sys.exit(1)
elif os.path.exists("firebase-adminsdk.json"):
    # Fallback for local testing if file exists
    cred = credentials.Certificate("firebase-adminsdk.json")
else:
    logger.error("No Firebase credentials found! Set FIREBASE_SERVICE_ACCOUNT env var or provide firebase-adminsdk.json")
    sys.exit(1)

try:
    initialize_app(cred)
    db = firestore.client()
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {e}")
    sys.exit(1)

# Collection Name in Firestore
COLLECTION_NAME = "authorized_groups"

# --- PRODUCT LIST TEXT ---
DEFAULT_PRODUCT_LIST = """
💳 ᑌᑎᎥᑭᎥᑎ ᐯᗩOᑕᕼᗴᖇ - 𝙋𝙧𝙞𝙘𝙚 𝙇𝙞𝙨𝙩  
━━━━━━━━━━━━━━  
☞ 20   🆄🅲  ➪  19 𝐁ᴀɴᴋ  
☞ 36   🆄🅲  ➪  34 𝐁ᴀɴᴋ  
☞ 80   🆄🅲  ➪  74 𝐁ᴀɴᴋ  
☞ 160  🆄🅲  ➪  147 𝐁ᴀɴᴋ  
☞ 161  🆄🅲  ➪  148 𝐁ᴀɴᴋ  
☞ 405  🆄🅲  ➪  372 𝐁ᴀɴᴋ  
☞ 800  🆄🅲  ➪  733 𝐁ᴀɴᴋ  
☞ 810  🆄🅲  ➪  743 𝐁ᴀɴᴋ  
☞ 1625 🆄🅲  ➪  1490 𝐁ᴀɴᴋ  
☞ 2000 🆄🅲  ➪  1855 𝐁ᴀɴᴋ  
━━━━━━━━━━━━━━  

🛍️ 𝑺𝒑𝒆𝒄𝒊𝒂𝒍 𝑰𝒕𝒆𝒎  
┏━━━━━━━━━━━━━━━┓  
┃ 🎟️ Weekly Lite ➪ 36 𝐁ᴀɴᴋ  
┗━━━━━━━━━━━━━━━┛  
☞ Level Up-6   ➪ 37 𝐁ᴀɴᴋ  
☞ Level Up-10 ➪ 62 𝐁ᴀɴᴋ  
☞ Level Up-15 ➪ 62 𝐁ᴀɴᴋ  
☞ Level Up-20 ➪ 62 𝐁ᴀɴᴋ  
☞ Level Up-25 ➪ 62 𝐁ᴀɴᴋ  
☞ Level Up-30 ➪ 88 𝐁ᴀɴᴋ  
━━━━━━━━━━━━━━  

🌟 Evo Access:  
☞ Evo 3 Day ➪ 66 𝐁ᴀɴᴋ  
☞ Evo 7 Day ➪ 100 𝐁ᴀɴᴋ  
☞ Evo 30 Day ➪ 290 𝐁ᴀɴᴋ  
━━━━━━━━━━━━━━  

╭─❖ 𝐆𝐚𝐫𝐞𝐧𝐚 𝐒𝐢𝐧𝐠𝐚𝐩𝐨𝐫𝐞 Տᕼᗴᒪᒪ ❖─╮  
│ 🎏 50 Shell SG   ➪ 125 𝐁ᴀɴᴋ  
│ 🎏 100 Shell SG  ➪ 245 𝐁ᴀɴᴋ  
│ 🎏 320 Shell SG  ➪ 760 𝐁ᴀɴᴋ  
╰─────────────────────╯  

╭─❖ 𝐆𝐚𝐫𝐞𝐧𝐚 𝐈𝐧𝐝𝐨𝐧𝐞𝐬𝐢𝐚 Տᕼᗴᒪᒪ ❖─╮  
│ 🔮 33 Shell ID   ➪  80 𝐁ᴀɴᴋ  
│ 🔮 66 Shell ID   ➪ 155 𝐁ᴀɴᴋ  
│ 🔮 165 Shell ID  ➪ 370 𝐁ᴀɴᴋ  
│ 🔮 330 Shell ID  ➪ 680 𝐁ᴀɴᴋ  
╰─────────────────────╯  

☞︎︎︎ 𝑆𝑀 𝑃𝑎𝑦𝑚𝑒𝑛𝑡 ➪ +0.00%
"""

# --- TELETHON CLIENT ---
if not API_ID or not API_HASH or not SESSION_STRING:
    logger.error("Missing API_ID, API_HASH or SESSION_STRING environment variables.")
    sys.exit(1)

client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)

# --- COMMAND HANDLERS ---

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.adduser$"))
async def add_user_handler(event):
    """
    Adds the other user in the group to the database.
    """
    chat = await event.get_chat()
    chat_id = str(chat.id)
    
    # Logic to find the 'other' user in a private group or small group
    participants = await client.get_participants(chat)
    target_user = None
    
    for user in participants:
        if not user.is_self and not user.bot:
            target_user = user
            break
    
    if not target_user:
        await event.edit("⚠️ **Error:** No eligible user found in this group to add.")
        return

    try:
        # Prepare data for Firestore
        data = {
            "user_id": target_user.id,
            "user_name": target_user.first_name,
            "allowed_group_id": chat_id,
            "balance_bdt": 0.0,
            "balance_usdt": 0.0,
            "product_list": DEFAULT_PRODUCT_LIST,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        
        # Store in Firestore using Chat ID as the Document ID
        db.collection(COLLECTION_NAME).document(chat_id).set(data)
        
        success_msg = (
            f"✅ **User Added Successfully!**\n\n"
            f"👤 **User:** {target_user.first_name} (`{target_user.id}`)\n"
            f"🆔 **Group ID:** `{chat_id}`\n"
            f"💰 **Initial Balance:** 0 BDT"
        )
        await event.edit(success_msg)
        
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        await event.edit(f"❌ **Error:** {str(e)}")


@client.on(events.NewMessage(outgoing=True, pattern=r"^\.removeuser$"))
async def remove_user_handler(event):
    """
    Removes the user details associated with this group from the database.
    """
    chat_id = str(event.chat_id)
    
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(chat_id)
        doc = doc_ref.get()
        
        if doc.exists:
            doc_ref.delete()
            await event.edit("🗑️ **User and Group data removed from database.**")
        else:
            await event.edit("⚠️ **Error:** No authorized user found for this group.")
            
    except Exception as e:
        logger.error(f"Error removing user: {e}")
        await event.edit(f"❌ **Error:** {str(e)}")


@client.on(events.NewMessage(outgoing=True, pattern=r"^\.addbalance (\d+(\.\d+)?)$"))
async def add_balance_handler(event):
    """
    Adds BDT balance to the user associated with this group.
    Usage: .addbalance 500
    """
    chat_id = str(event.chat_id)
    amount = float(event.pattern_match.group(1))
    
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(chat_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            await event.edit("⚠️ **Error:** This group is not authorized. Use `.adduser` first.")
            return
        
        current_data = doc.to_dict()
        current_balance = current_data.get("balance_bdt", 0.0)
        new_balance = current_balance + amount
        
        doc_ref.update({"balance_bdt": new_balance})
        
        msg = (
            f"💰 **Balance Added!**\n\n"
            f"➕ Added: {amount} BDT\n"
            f"💵 New Balance: {new_balance} BDT"
        )
        await event.edit(msg)
        
    except Exception as e:
        logger.error(f"Error adding balance: {e}")
        await event.edit(f"❌ **Error:** {str(e)}")


@client.on(events.NewMessage(outgoing=True, pattern=r"^\.deductbalance (\d+(\.\d+)?)$"))
async def deduct_balance_handler(event):
    """
    Deducts BDT balance from the user associated with this group.
    Usage: .deductbalance 100
    """
    chat_id = str(event.chat_id)
    amount = float(event.pattern_match.group(1))
    
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(chat_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            await event.edit("⚠️ **Error:** This group is not authorized. Use `.adduser` first.")
            return
        
        current_data = doc.to_dict()
        current_balance = current_data.get("balance_bdt", 0.0)
        new_balance = current_balance - amount
        
        doc_ref.update({"balance_bdt": new_balance})
        
        msg = (
            f"💸 **Balance Deducted!**\n\n"
            f"➖ Deducted: {amount} BDT\n"
            f"💵 New Balance: {new_balance} BDT"
        )
        await event.edit(msg)
        
    except Exception as e:
        logger.error(f"Error deducting balance: {e}")
        await event.edit(f"❌ **Error:** {str(e)}")

# --- MAIN EXECUTION ---
def main():
    print("--- Starting Bot ---")
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("--- Flask Server Started ---")

    # Start Telethon
    with client:
        client.run_until_disconnected()

if __name__ == '__main__':
    main()
