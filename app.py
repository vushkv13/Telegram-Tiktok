from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
import os
import requests
from douyin_tiktok_scraper.scraper import Scraper
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

api = Scraper()
token = os.getenv("TOKEN")
BOT_USERNAME = '@TikTokv_vbot'

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received start command")
    await update.message.reply_text('Привет! Отправь мне ссылку на ТикТок видео')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received help command")
    await update.message.reply_text('Please type something so I can respond')

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received custom command")
    await update.message.reply_text('This is a custom command')

async def hybrid_parsing(url: str):
    try:
        logger.info(f"Parsing URL: {url}")
        result = await api.hybrid_parsing(url)
        
        if not result:
            logger.error(f"No result returned for URL: {url}")
            return None

        logger.info(f"Parsing result: {result}")

        video_data = result.get("video_data")
        music_data = result.get("music")

        if not video_data or not music_data:
            logger.error(f"Missing video_data or music_data in the result for URL: {url}")
            return None

        video = video_data.get("nwm_video_url_HQ")
        video_hq = video_data.get("nwm_video_url_HQ")
        music = music_data.get("play_url", {}).get("uri")
        caption = result.get("desc")

        logger.info(f"Video URL: {video}")
        logger.info(f"Video HQ URL: {video_hq}")
        logger.info(f"Music URL: {music}")
        logger.info(f"Caption: {caption}")

        if not video or not video_hq or not music or not caption:
            logger.error(f"Incomplete data for URL: {url}")
            return None

        response_video = requests.get(video)
        response_video_hq = requests.get(video_hq)

        if response_video.status_code == 200:
            video_stream = BytesIO(response_video.content)
        else:
            logger.error(f"Failed to download video. Status code: {response_video.status_code}")
            return None

        if response_video_hq.status_code == 200:
            video_stream_hq = BytesIO(response_video_hq.content)
        else:
            logger.error(f"Failed to download high quality video. Status code: {response_video_hq.status_code}")
            return None

        return video_stream, video_stream_hq, music, caption, video_hq
    except Exception as e:
        logger.error(f'An error occurred: {str(e)}')
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    logger.info(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
        else:
            return
    elif message_type == 'private':
        if "tiktok.com" in text:
            result = await hybrid_parsing(text)
            if result:
                video, video_hq, music, caption, link = result
                text = f"Link:\n{link}\n\nSound:\n{music}\n\nCaption:\n{caption}"
                text_link = f"Video is too large, sending link instead\n\nLink:\n{link}\n\nSound:\n{music}\n\nCaption:\n{caption}"

                try:
                    await update.message.reply_video(video=InputFile(video_hq), caption=text)
                except Exception as e:
                    logger.error(f"An error occurred while sending video: {str(e)}")
                    if "Request Entity Too Large (413)" in str(e):
                        logger.info("Video is too large, sending link instead")
                        await update.message.reply_text(text_link)
                    else:
                        await update.message.reply_text("An error occurred while sending the video. Please try again later.")
            else:
                await update.message.reply_text("An error occurred while parsing the TikTok URL. Please ensure the URL is correct and try again.")
        else:
            await update.message.reply_text("Please send a TikTok URL")
            return

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    logger.info('Starting bot...')
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
    logger.info('Polling...')
    app.run_polling(poll_interval=3)
