from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
import os
import requests
from pytiktok import TikTokApi  # Импортируем TikTokApi
from dotenv import load_dotenv
import logging

logging.getLogger().setLevel(logging.CRITICAL)
load_dotenv()

api = TikTokApi()  # Инициализируем TikTokApi
token = os.getenv("TOKEN")
BOT_USERNAME = '@TikTokv_vbot'

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Support me on : https://www.paypal.me/ardha27')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Please type something so i can respond')

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is custom command')

async def hybrid_parsing(url: str) -> dict:
    try:
        # Извлекаем ID видео из URL
        video_id = url.split('/')[-1]
        if '?' in video_id:
            video_id = video_id.split('?')[0]

        # Получаем видео без водяного знака
        video = api.video(id=video_id, no_watermark=True)

        if video:
            video_url = video['video']['download_addr']
            caption = video['desc']
            music = video['music']['play_url']

            response_video = requests.get(video_url)
            if response_video.status_code == 200:
                video_stream = BytesIO(response_video.content)
            else:
                print(f"Failed to download MP4. Status code: {response_video.status_code}")
                video_stream = None

            return video_stream, music, caption

    except Exception as e:
        print(f'An error occurred: {str(e)}')
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
        else:
            return
    elif message_type == 'private':
        if "tiktok.com" in text:
            result = await hybrid_parsing(text)

            if result:
                video_stream = result[0]
                music = result[1]
                caption = result[2]

                if video_stream:
                    try:
                        await update.message.reply_video(video=InputFile(video_stream), caption=caption)
                    except Exception as e:
                        if "Request Entity Too Large (413)" in str(e):
                            print("Video is too large, sending link instead")
                            await update.message.reply_text(f"Video is too large, caption: {caption}")
                else:
                    await update.message.reply_text("Failed to download the video.")
            else:
                await update.message.reply_text("An error occurred while parsing the TikTok URL. Please ensure the URL is correct and try again.")
        else:
            await update.message.reply_text("Please send a TikTok URL")
            return

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)
