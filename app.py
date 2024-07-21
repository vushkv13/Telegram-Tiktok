from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
import os
import requests
from douyin_tiktok_scraper.scraper import Scraper
from dotenv import load_dotenv
import logging
import tenacity

logging.getLogger().setLevel(logging.CRITICAL)
load_dotenv()

api = Scraper()
token = os.getenv("TOKEN")
BOT_USERNAME = '@TikTokv_vbot'

@tenacity.retry_on_exception(stop_after_attempt=5, wait=fixed(10))
def hybrid_parsing(url: str) -> dict:
    try:
        # Hybrid parsing(Douyin/TikTok URL)
        result = api.hybrid_parsing(url)

        video = result["video_data"]["nwm_video_url_HQ"]
        video_hq = result["video_data"]["nwm_video_url_HQ"]
        music = result["music"]["play_url"]["uri"]
        caption = result["desc"]

        print("Video URL:", video)
        print("Video_HQ URL:", video_hq)
        print("Play URL:", music)
        print("Caption:", caption)

        response_video = requests.get(video)
        response_video_hq = requests.get(video_hq)

        if response_video.status_code == 200:
            video_stream = BytesIO(response_video.content)
        else:
            print(f"Failed to download MP4. Status code: {response_video.status_code}")

        if response_video_hq.status_code == 200:
            video_stream_hq = BytesIO(response_video_hq.content)
        else:
            print(f"Failed to download MP4. Status code: {response_video_hq.status_code}")

    except Exception as e:
        print(f'An error occurred: {str(e)}')
        raise e

    return video_stream, video_stream_hq, music, caption, video_hq

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text('Support me on : https://www.paypal.me/ardha27')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text('Please type something so i can respond')

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text('This is custom command')

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

      try:
          result = hybrid_parsing(text)

          if result:
              video = result[0]
              video_hq = result[1]
              music = result[2]
              caption = result[3]
              link = result[4]
              text = "Link:\n" + link + "\n\n" + "Sound:\n" + music + "\n\n" + "Caption:\n" + caption
              text_link = "Video is too large, sending link instead" + "\n\n" + "Link:\n" + link + "\n\n" + "Sound:\n" + music + "\n\n" + "Caption:\n" + caption

              try:
                  await update.message.reply_video(video=InputFile(video_hq), caption=text)
                except Exception as e:
                  if "Request Entity Too Large (413)" in str(e):
                      print("Video is too large, sending link instead")
                      await update.message.reply
