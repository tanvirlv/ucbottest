import os
import sys
import asyncio
import logging
from datetime import datetime
from flask import Flask, jsonify
from threading import Thread
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat
import re

# Configure encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Logging setup
logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import configurations and database
from config import API_ID, API_HASH, SESSION_STRING, ADMIN_USER_IDS
from firestore_db import db

# Flask app for keeping the bot alive
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "Bot is running", "timestamp": datetime.now().isoformat()})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# Telegram Client
client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH
)

# Helper Functions
async def get_other_user_in_group(event):
    """Get the other user in the group (excluding bot and command sender)"""
    try:
        chat = await event.get_chat()
        
        if hasattr(chat, 'participants_count') or isinstance(chat, (Channel, Chat)):
            # For groups/channels
            participants = await client.get_participants(chat)
            
            # Filter out bot and command sender
            other_users = []
            for participant in participants:
                # Skip if it's the bot itself
                if participant.id == (await client.get_me()).id:
                    continue
                # Skip if it's the command sender
                if participant.id == event.sender_id:
                    continue
                # Skip if it's a bot
                if participant.bot:
                    continue
                
                other_users.append(participant)
            
            return other_users
        else:
            # For private chats
            return []
    except Exception as e:
        logger.error(f"Error getting participants: {e}")
        return []

async def is_admin(event):
    """Check if the sender is an admin"""
    return event.sender_id in ADMIN_USER_IDS

async def is_group_admin(event):
    """Check if sender is admin in the group"""
    try:
        if event.is_group:
            chat = await event.get_chat()
            participant = await client.get_permissions(entity=chat, user=event.sender_id)
            return participant.is_admin
    except:
        pass
    return False

# Event Handlers
@client.on(events.NewMessage(pattern=r'^\.adduser$'))
async def add_user_handler(event):
    """Handle .adduser command"""
    try:
        # Check if sender is admin
        if not await is_admin(event):
            await event.reply("❌ You are not authorized to use this command!")
            return
        
        # Check if in group
        if not event.is_group:
            await event.reply("❌ This command can only be used in groups!")
            return
        
        # Get other users in the group
        other_users = await get_other_user_in_group(event)
        
        if not other_users:
            await event.reply("❌ No other users found in this group to add!")
            return
        
        if len(other_users) > 1:
            await event.reply("❌ Multiple users found. Please specify which user to add!")
            return
        
        user_to_add = other_users[0]
        chat_id = event.chat_id
        
        # Check if user already exists and is allowed
        existing_user = await db.get_user(user_to_add.id)
        if existing_user:
            allowed_groups = existing_user.get("allowed_groups", [])
            if str(chat_id) in allowed_groups:
                await event.reply(f"✅ User @{user_to_add.username or user_to_add.id} is already allowed in this group!")
                return
        
        # Add user to database
        result = await db.add_user(
            user_id=user_to_add.id,
            chat_id=chat_id,
            username=user_to_add.username,
            full_name=f"{user_to_add.first_name or ''} {user_to_add.last_name or ''}".strip()
        )
        
        if result == "created":
            await event.reply(f"✅ User @{user_to_add.username or user_to_add.id} has been added successfully!\n"
                             f"💰 Initial Balance: 0 TK | 0 USDT\n"
                             f"📊 Groups Allowed: 1")
        elif result == "updated":
            await event.reply(f"✅ User @{user_to_add.username or user_to_add.id} has been granted access to this group!")
        else:
            await event.reply("❌ Failed to add user!")
            
    except Exception as e:
        logger.error(f"Error in add_user_handler: {e}")
        await event.reply("❌ An error occurred while processing your request!")

@client.on(events.NewMessage(pattern=r'^\.removeuser$'))
async def remove_user_handler(event):
    """Handle .removeuser command"""
    try:
        # Check if sender is admin
        if not await is_admin(event):
            await event.reply("❌ You are not authorized to use this command!")
            return
        
        # Check if in group
        if not event.is_group:
            await event.reply("❌ This command can only be used in groups!")
            return
        
        # Get other users in the group
        other_users = await get_other_user_in_group(event)
        
        if not other_users:
            await event.reply("❌ No other users found in this group to remove!")
            return
        
        if len(other_users) > 1:
            await event.reply("❌ Multiple users found. Please specify which user to remove!")
            return
        
        user_to_remove = other_users[0]
        chat_id = event.chat_id
        
        # Remove user from database for this group
        result = await db.remove_user(user_to_remove.id, chat_id)
        
        if result == "removed_from_group":
            await event.reply(f"✅ User @{user_to_remove.username or user_to_remove.id} has been removed from this group!")
        elif result == "deleted_completely":
            await event.reply(f"✅ User @{user_to_remove.username or user_to_remove.id} has been completely removed from the system!")
        elif result == "user_not_in_group":
            await event.reply(f"❌ User @{user_to_remove.username or user_to_remove.id} is not allowed in this group!")
        elif result == "user_not_found":
            await event.reply(f"❌ User @{user_to_remove.username or user_to_remove.id} not found in the system!")
        else:
            await event.reply("❌ Failed to remove user!")
            
    except Exception as e:
        logger.error(f"Error in remove_user_handler: {e}")
        await event.reply("❌ An error occurred while processing your request!")

# User Commands (Example - You can add more later)
@client.on(events.NewMessage(pattern=r'^\.balance$'))
async def balance_handler(event):
    """Check user balance"""
    try:
        # Check if user is allowed in this group
        if event.is_group:
            if not await db.is_user_allowed(event.sender_id, event.chat_id):
                await event.reply("❌ You are not authorized to use the bot in this group!")
                return
        
        user_data = await db.get_user(event.sender_id)
        
        if not user_data:
            await event.reply("❌ You are not registered in the system!")
            return
        
        balance_tk = user_data.get("balance_tk", 0)
        balance_usdt = user_data.get("balance_usdt", 0)
        
        await event.reply(
            f"💰 **Your Balance**\n"
            f"──────────────\n"
            f"📊 TK: {balance_tk:.2f}\n"
            f"📊 USDT: {balance_usdt:.2f}\n"
            f"──────────────\n"
            f"🆔 User ID: {event.sender_id}"
        )
        
    except Exception as e:
        logger.error(f"Error in balance_handler: {e}")
        await event.reply("❌ An error occurred!")

@client.on(events.NewMessage(pattern=r'^\.help$'))
async def help_handler(event):
    """Show help message"""
    help_text = """
🤖 **Voucher Trading Bot** 🤖

👑 **Admin Commands:**
`.adduser` - Add a user to this group
`.removeuser` - Remove a user from this group

👤 **User Commands:**
`.balance` - Check your balance
`.help` - Show this help message

📊 **Features:**
• Buy/Sell vouchers
• Balance management
• Multi-group support

💡 More commands coming soon!
    """
    await event.reply(help_text)

# Start command
@client.on(events.NewMessage(pattern=r'^/start$'))
async def start_handler(event):
    """Handle /start command"""
    welcome_text = """
🎉 **Welcome to Voucher Trading Bot!** 🎉

I'm a bot for buying and selling vouchers with secure transactions.

📋 **Available Commands:**
`.help` - Show all commands
`.balance` - Check your balance

👑 Admin users have additional commands for managing users in groups.

Start trading vouchers today! 🚀
    """
    await event.reply(welcome_text)

async def main():
    """Main function to start the bot"""
    await client.start()
    logger.info("Bot started successfully!")
    await client.run_until_disconnected()

# In main.py, modify the Flask run section:
if __name__ == '__main__':
    # Get port from Render environment (8080 default)
    port = int(os.environ.get("PORT", 8080))
    
    # ... [rest of your code remains the same]
    def run_flask():
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
