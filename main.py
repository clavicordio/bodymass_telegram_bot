import asyncio
import logging.handlers
import os
import sys
from datetime import datetime

from telebot.async_telebot import AsyncTeleBot
from telebot import types
from telebot import logger

from src.glossary import *
from src.conversationdata import get_conversation_data, write_conversation_data, ConversationState
from src.datautils import plot_user_data, add_record_now, date_format, user_data_to_csv, user_data_from_csv_url, delete_user_data
from src.datautils import CSVParsingError
import src.config


bot = AsyncTeleBot(src.config.TELEGRAM_TOKEN)

logger.setLevel(logging.DEBUG)
os.makedirs('logs', exist_ok=True)
fh = logging.handlers.TimedRotatingFileHandler('logs/log', when='midnight')
fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s'))
logger.addHandler(fh)


@bot.message_handler(content_types=['document'])
@bot.message_handler(func=lambda _: True)
async def handler(message):
    logger.info("Message from %s: %s", message.chat.id, message.text)
    try:
        user_data = await get_conversation_data(message.chat.id)
        await reply(message, user_data)
    except Exception as exception:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.critical("Unexpected error [%s:%d]: %s: %s" % (fname, exc_tb.tb_lineno, type(exception).__name__,
                                                              exception))


def reply_markup(buttons):
    markup = types.ReplyKeyboardMarkup()
    markup.row(*buttons)
    markup.one_time_keyboard = True
    return markup


DEFAULT_MARKUP = reply_markup([ENTER_WEIGHT_BUTTON, SHOW_MENU_BUTTON])


async def reply(message: types.Message, user_data: dict):
    logger.debug("User data:"+str(user_data))

    conversation_state = user_data['conversation_state']

    message_text = message.text.strip() if message.text is not None else ''

    if message_text:
        if message_text == '/info':
            await reply_info(message, user_data)
        elif message_text in ENTER_WEIGHT_COMMANDS:
            await reply_enter_weight(message, user_data)
        elif message_text in SHOW_MENU_COMMANDS:
            await reply_start(message, user_data)
        elif message_text == '/plot':
            await reply_plot(message, user_data)
        elif message_text == '/plot_all':
            await reply_plot_all(message, user_data)
        elif message_text == '/download':
            await reply_download(message, user_data)
        elif message_text == '/upload':
            await reply_upload(message, user_data)
        elif message_text == '/erase':
            await reply_erase(message, user_data)
        elif conversation_state == ConversationState.awaiting_body_weight:
            await reply_body_weight(message, user_data)
        elif conversation_state == ConversationState.awaiting_erase_confirmation:
            await reply_erase_confirmation(message, user_data)
        elif conversation_state == ConversationState.awaiting_csv_table:
            await reply_csv_table(message, user_data)
        elif message.document is not None:
            await reply_unexpected_document(message, user_data)
        elif conversation_state == ConversationState.init:
            await reply_start(message, user_data)
        else:
            assert False, "Conversation state assertion"
    else:
        if conversation_state == ConversationState.awaiting_csv_table:
            await reply_csv_table(message, user_data)
        elif message.document is not None:
            await reply_unexpected_document(message, user_data)

    await write_conversation_data(message.chat.id, user_data)


async def reply_info(message: types.Message, user_data: dict):
    text = "This bot is designed to track body weight and will help you on your fitness journey. " \
           "Simply weigh yourself regularly and send me the results.\n\n" \
           "Your body weight highly varies from day to day (up to ~3 kg). " \
           "This happens mainly due to food and fluid retention. " \
           "So if you weigh yourself one day, then simply look at the scales the other day, unfortunately " \
           "you will not get any insights on how many kilos of tissue you actually gained or lost. " \
           "To track your progress " \
           "efficiently you need to measure your body mass at least <b>3 times a week (ideally, every day)</b> and " \
           "write down the results. " \
           "It is also recommended to weigh yourself approximately at the same hour of day. " \
           "After doing this for at least 2 weeks straight, you need to look at the " \
           "<a href=\"https://en.wikipedia.org/wiki/Trend_line_(technical_analysis)\">trend line</a>. " \
           "This way you will get a real picture of what is going on - are you losing or gaining weight, " \
           "and at what speed. \n\n" \
           "The mission of this bot is to make this process <b>as effortless as possible</b>. " \
           "Just pull out your phone and send me a couple of digits. " \
           "This is as easy as it gets. " \
           "Remember, fitness is all about building momentum, and <b>the less unnecessary " \
           "resistance you meet, the more sustainable your habits become in the long run.</b>\n\n" \
           "By the way, the general guideline is you should aim " \
           "at <b>0.5-1 kg per week</b> for <b>weight loss</b>, " \
           "and at <b>0.2-0.5 kg per week</b> for <b>bulking</b> if you want to do this without health risks. " \
           "But it is a better idea to consult a coach or nutritionist since these numbers depend" \
           "on a variety of factors (sex, age, overall health). "

    await bot.send_message(message.chat.id, text,
                           reply_markup=DEFAULT_MARKUP,
                           parse_mode="HTML",
                           disable_web_page_preview=True)
    user_data['conversation_state'] = ConversationState.init


async def reply_start(message: types.Message, user_data: dict):
    text = "Hello, I am a bot designed to track body weight and help you reach fitness goals. " \
           "Please select a command below.\n\n"
    text += COMMAND_LIST

    await bot.send_message(message.chat.id, text, reply_markup=DEFAULT_MARKUP, parse_mode="HTML")
    user_data['conversation_state'] = ConversationState.init


async def reply_enter_weight(message: types.Message, user_data):
    text = "How much do you weigh today?"
    await bot.send_message(message.chat.id, text, parse_mode="HTML")
    user_data['conversation_state'] = ConversationState.awaiting_body_weight


async def reply_body_weight(message: types.Message, user_data):
    try:
        body_weight = float(message.text.strip())
        if not (0 < body_weight < src.config.MAX_BODY_WEIGHT):
            raise ValueError
    except ValueError:
        await bot.reply_to(message, "Please enter a valid positive number (your body mass in kg) /start")
        return

    await add_record_now(message.chat.id, body_weight)
    img_path, speed_week_kg = await plot_user_data(message.chat.id, only_two_weeks=True)
    with open(img_path, 'rb') as img_file_object:
        text = f"Successfully added a new entry:\n<b>{datetime.now().strftime(date_format)} - {body_weight} kg</b>\n"
        if speed_week_kg is not None:
            if speed_week_kg > 0:
                text += "\nYou are currently in a <i>calorie surplus</i>.\n"
                text += "You are gaining weight at an average rate of <i>%.2f kg/week</i>\n" % speed_week_kg
            elif speed_week_kg <= 0:
                text += "\nYou are currently in a <i>calorie deficit</i>.\n"
                text += "You are losing weight at an average rate of <i>%.2f kg/week</i>\n" % abs(speed_week_kg)

        await bot.send_photo(message.chat.id, caption=text,
                             photo=img_file_object,
                             reply_markup=DEFAULT_MARKUP,
                             reply_to_message_id=message.id,
                             parse_mode='HTML')

    try:
        os.remove(img_path)
    except OSError:
        pass
    user_data['conversation_state'] = ConversationState.init


async def reply_plot(message: types.Message, user_data: dict):
    img_path, speed_week_kg = await plot_user_data(message.chat.id, only_two_weeks=True)
    with open(img_path, 'rb') as img_file_object:
        text = "Here's a plot of your progress over the last two weeks.\n"
        if speed_week_kg is not None:
            if speed_week_kg > 0:
                text += "\nYou are currently in a <i>calorie surplus</i>.\n"
                text += "You are gaining weight at an average rate of <i>%.2f kg/week</i>\n" % speed_week_kg
            elif speed_week_kg <= 0:
                text += "\nYou are currently in a <i>calorie deficit</i>.\n"
                text += "You are losing weight at an average rate of <i>%.2f kg/week</i>\n" % abs(speed_week_kg)

        await bot.send_photo(message.chat.id, caption=text,
                             photo=img_file_object,
                             reply_markup=DEFAULT_MARKUP,
                             reply_to_message_id=message.id,
                             parse_mode='HTML')
    try:
        os.remove(img_path)
    except OSError:
        pass
    user_data['conversation_state'] = ConversationState.init


async def reply_plot_all(message: types.Message, user_data: dict):
    img_path, speed_week_kg = await plot_user_data(message.chat.id, only_two_weeks=False)
    with open(img_path, 'rb') as img_file_object:
        text = "Here's a plot of your overall progress.\n"
        if speed_week_kg is not None:
            if speed_week_kg > 0:
                text += "\nYou are in a <i>calorie surplus</i>.\n"
                text += "You are gaining weight at an average rate of <i>%.2f kg/week</i>\n" % speed_week_kg
            elif speed_week_kg <= 0:
                text += "\nYou are in a <i>calorie deficit</i>.\n"
                text += "You are losing weight at an average rate of <i>%.2f kg/week</i>\n" % abs(speed_week_kg)

        await bot.send_photo(message.chat.id, caption=text,
                             photo=img_file_object,
                             reply_markup=DEFAULT_MARKUP,
                             reply_to_message_id=message.id,
                             parse_mode='HTML')
    try:
        os.remove(img_path)
    except OSError:
        pass

    user_data['conversation_state'] = ConversationState.init


async def reply_download(message: types.Message, user_data: dict):
    csv_file_path = await user_data_to_csv(message.chat.id)
    file_size = os.path.getsize(csv_file_path)
    if file_size == 0:
        text = "You don't have any data to download yet.\n\n" \
               "Use /enter_weight daily. \n" \
               "Alternatively, use /upload to upload your existing data."
        await bot.reply_to(message, text, reply_markup=DEFAULT_MARKUP)
    else:
        text = "<b>Here is all of your data.</b>"
        text += "You can either analyze it by yourself, or use it as a backup to " \
                "/upload it in case of the data loss."
        with open(csv_file_path, 'rb') as csv_file_object:
            await bot.send_document(chat_id=message.chat.id,
                                    reply_to_message_id=message.id,
                                    reply_markup=DEFAULT_MARKUP,
                                    document=csv_file_object,
                                    parse_mode='HTML',
                                    caption=text)
    try:
        os.remove(csv_file_path)
    except OSError:
        pass

    user_data['conversation_state'] = ConversationState.init


async def reply_upload(message: types.Message, user_data: dict):
    text = "You can upload your existing body weight data by giving me a *.csv table."
    text += "The table should contain two columns:\n"
    text += "- Date in the " + date_format + " format\n"
    text += "- Body weight\n"
    text += "You can download an example by using /download command. \n\n"
    text += "To proceed with uploading, please send me a valid *.csv file."

    text += "\n\n/start - return to menu"

    await bot.reply_to(message, text)
    user_data['conversation_state'] = ConversationState.awaiting_csv_table


async def reply_csv_table(message: types.Message, user_data: dict):
    document = message.document
    if document is None:
        await bot.reply_to(message, "I didn't get a valid document.\n/start")
        return

    file_id = document.file_id
    file_size = document.file_size
    if file_size > src.config.MAX_FILE_SIZE:
        await bot.reply_to(message, f"File is too big (max size {src.config.MAX_FILE_SIZE // 1024} kb)"
                                    f"\n/start")
        return

    file_info = await bot.get_file(file_id)
    file_url = 'https://api.telegram.org/file/bot{0}/{1}'.format(src.config.TELEGRAM_TOKEN, file_info.file_path)

    try:
        await user_data_from_csv_url(message.chat.id, file_url, src.config.MAX_BODY_WEIGHT)
    except CSVParsingError:
        await bot.reply_to(message, "The file is invalid. Please use /download to get an example of a valid file."
                                    "\n/start")
        return
    except Exception as exception:
        await bot.reply_to(message, "Unexpected error occurred during your file processing. I'm sorry."
                                    "\n/start")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.critical("Unexpected error while processing CSV file [%s:%d]: %s: %s" % (fname, exc_tb.tb_lineno, type(exception).__name__,
                                                              exception))

        return

    img_path, speed_week_kg = await plot_user_data(message.chat.id, only_two_weeks=False)
    with open(img_path, 'rb') as img_file_object:
        text = "<b>Data has been uploaded successfully.</b>\nTake a look at the plot."
        await bot.send_photo(message.chat.id, caption=text,
                             photo=img_file_object,
                             reply_markup=DEFAULT_MARKUP,
                             reply_to_message_id=message.id,
                             parse_mode='HTML')

    user_data['conversation_state'] = ConversationState.init
    try:
        os.remove(img_path)
    except OSError:
        pass


async def reply_erase(message: types.Message, user_data: dict):
    text = 'You are about to <b>erase all of your data</b>. '
    text += 'This cannot be undone.\n\n'
    text += '<b>Please confirm by typing <i>yes</i></b>.\n\n'
    text += '/start - return'
    await bot.reply_to(message, text, parse_mode='HTML')
    user_data['conversation_state'] = ConversationState.awaiting_erase_confirmation


async def reply_erase_confirmation(message, user_data: dict):
    if message.text.strip().lower() != 'yes':
        text = 'Ok, cancelling the deletion.'
        await bot.reply_to(message, text, reply_markup=DEFAULT_MARKUP)
        user_data['conversation_state'] = ConversationState.init
        return

    csv_file_path = await user_data_to_csv(message.chat.id)
    await delete_user_data(message.chat.id)

    file_size = os.path.getsize(csv_file_path)
    if file_size == 0:
        text = "You don't have any data yet."
        await bot.reply_to(message, text, reply_markup=DEFAULT_MARKUP)
        user_data['conversation_state'] = ConversationState.init
        return

    text = 'Ok, I have forgotten everything about your progress.\n'\
           'But grab the file with your erased data, just in case.'

    with open(csv_file_path, 'rb') as csv_file_object:
        await bot.send_document(chat_id=message.chat.id,
                                reply_to_message_id=message.id,
                                reply_markup=DEFAULT_MARKUP,
                                document=csv_file_object,
                                caption=text)
    try:
        os.remove(csv_file_path)
    except OSError:
        pass
    user_data['conversation_state'] = ConversationState.init


async def reply_unexpected_document(message: types.Message, user_data: dict):
    text = "That is an unexpected document. Do you want me to upload your body weight data? Use the /upload command."
    await bot.reply_to(message, text, reply_markup=DEFAULT_MARKUP)
    user_data['conversation_state'] = ConversationState.init

asyncio.run(bot.polling(non_stop=True))
