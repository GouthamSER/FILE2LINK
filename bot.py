import os
import requests
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.environ.get("API_ID", "123456"))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")

app = Client("file_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

Gofile_API = "https://api.gofile.io/uploadFile"


@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "👋 Send me any file (up to 5GB) and I will give you a **streamable & downloadable link**!"
    )


@app.on_message(filters.document | filters.audio | filters.video | filters.photo)
async def handle_file(client, message: Message):
    try:
        msg = await message.reply_text("⏳ Downloading your file...")
        file_path = await client.download_media(message, file_name=None)
        file_name = os.path.basename(file_path)

        await msg.edit_text("☁️ Uploading to GoFile.io (supports streaming)...")

        with open(file_path, "rb") as f:
            files = {"file": (file_name, f)}
            response = requests.post(Gofile_API, files=files, timeout=3600)

        if response.status_code == 200 and response.json()["status"] == "ok":
            download_page = response.json()["data"]["downloadPage"]
            direct_link = response.json()["data"]["directLink"]

            await msg.edit_text(
                f"✅ File uploaded successfully!\n\n"
                f"🌐 Download page (streamable): {download_page}\n"
                f"📥 Direct download: {direct_link}"
            )
        else:
            await msg.edit_text(f"❌ Upload failed. Try again later.\n{response.text}")

        os.remove(file_path)

    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}")


if __name__ == "__main__":
    print("Bot is running...")
    app.run()
