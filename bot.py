import os
import requests
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.environ.get("API_ID", "123456"))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")

app = Client("file_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
Gofile_API = "https://api.gofile.io/uploadFile"

CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB chunks


@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "👋 Send me any file (up to 5GB) and I will give you a streamable & downloadable link with live progress!"
    )


@app.on_message(filters.document | filters.audio | filters.video | filters.photo)
async def handle_file(client, message: Message):
    try:
        msg = await message.reply_text("⏳ Downloading your file...")

        # Determine filename for different media types
        if message.document:
            file_name = message.document.file_name
        elif message.video:
            file_name = message.video.file_name or "video.mp4"
        elif message.audio:
            file_name = message.audio.file_name or "audio.mp3"
        elif message.photo:
            file_name = "photo.jpg"
        else:
            await msg.edit_text("❌ Unsupported file type.")
            return

        # Download file
        file_path = await client.download_media(message, file_name=file_name)
        if not file_path:
            await msg.edit_text("❌ Failed to download the file.")
            return

        await msg.edit_text("☁️ Uploading to GoFile.io...")

        file_size = os.path.getsize(file_path)
        uploaded = 0

        # Custom generator to stream file in chunks with progress
        def file_chunk_generator(file_path):
            nonlocal uploaded
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    uploaded += len(chunk)
                    yield chunk

        # Streaming upload using requests
        with open(file_path, "rb") as f:
            class StreamWithProgress:
                def __init__(self, file_path):
                    self.f = open(file_path, "rb")
                    self.total = os.path.getsize(file_path)
                    self.uploaded = 0

                def __iter__(self):
                    return self

                def __next__(self):
                    chunk = self.f.read(CHUNK_SIZE)
                    if not chunk:
                        self.f.close()
                        raise StopIteration()
                    self.uploaded += len(chunk)
                    percent = int(self.uploaded * 100 / self.total)
                    # Update Telegram message every 5%
                    if percent % 5 == 0:
                        try:
                            app.loop.create_task(msg.edit_text(f"☁️ Uploading... {percent}%"))
                        except:
                            pass
                    return chunk

            files = {"file": (file_name, StreamWithProgress(file_path))}
            response = requests.post(Gofile_API, files=files, timeout=7200)

        if response.status_code == 200 and response.json()["status"] == "ok":
            download_page = response.json()["data"]["downloadPage"]
            direct_link = response.json()["data"]["directLink"]

            await msg.edit_text(
                f"✅ File uploaded successfully!\n\n"
                f"🌐 Streamable link: {download_page}\n"
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
