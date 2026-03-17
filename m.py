import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired

# --- CONFIGURATION ---
API_ID = 1234567  # Your API ID
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"

bot = Client("StringGenBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store temporary user data
user_data = {}

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        "Welcome! I can help you generate a Pyrogram v2 String Session.\n\n"
        "Please send your **Phone Number** with country code (e.g., +1234567890)"
    )

@bot.on_message(filters.text & filters.private)
async def handle_message(client, message: Message):
    user_id = message.from_user.id
    text = message.text

    # Step 1: Handle Phone Number
    if user_id not in user_data:
        try:
            # Create a temporary Pyrogram Client for the user
            temp_client = Client(":memory:", api_id=API_ID, api_hash=API_HASH)
            await temp_client.connect()
            
            code_hash = await temp_client.send_code(text)
            user_data[user_id] = {
                "client": temp_client,
                "phone": text,
                "hash": code_hash.phone_code_hash
            }
            await message.reply_text("OTP sent! Please send the code in this format: `1 2 3 4 5` (with spaces).")
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
            return

    # Step 2: Handle OTP
    elif "hash" in user_data[user_id]:
        data = user_data[user_id]
        temp_client = data["client"]
        otp = text.replace(" ", "") # Remove spaces if user added them

        try:
            await temp_client.sign_in(data["phone"], data["hash"], otp)
        except SessionPasswordNeeded:
            await message.reply_text("This account has 2FA enabled. Please send your **Cloud Password**.")
            user_data[user_id]["awaiting_2fa"] = True
            return
        except (PhoneCodeInvalid, PhoneCodeExpired):
            await message.reply_text("❌ Invalid or Expired OTP. Try /start again.")
            return

        await finish_session(temp_client, message)
        del user_data[user_id]

async def finish_session(temp_client, message):
    string_session = await temp_client.export_session_string()
    # Send session to Saved Messages for security
    await temp_client.send_message("me", f"**Pyrogram v2 String Session:**\n\n`{string_session}`")
    await message.reply_text("✅ Session generated! Check your **Saved Messages**.")
    await temp_client.disconnect()

bot.run()
