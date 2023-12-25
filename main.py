import asyncio
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

from telebot.async_telebot import AsyncTeleBot
from telebot import types
from telebot import logger

import src.glossary as glossary
from src.conversationdata import get_conversation_data, write_conversation_data, ConversationState
from src.datautils import plot_user_data, add_record_now, date_format, user_data_to_csv, user_data_from_csv_url, delete_user_data
from src.datautils import CSVParsingError
import src.config


bot = AsyncTeleBot(src.config.TELEGRAM_TOKEN)

logger.setLevel(logging.DEBUG)
os.makedirs('logs', exist_ok=True)
fh = logging.handlers.TimedRotatingFileHandler('logs/log', when='midnight', encoding='utf-8')
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


DEFAULT_MARKUP = reply_markup([glossary.ENTER_WEIGHT_BUTTON, glossary.SHOW_MENU_BUTTON])


async def reply(message: types.Message, user_data: dict):
    logger.debug("User data:"+str(user_data))

    conversation_state = user_data['conversation_state']

    message_text = message.text.strip() if message.text is not None else ''

    if message_text:
        if message_text == '/info':
            await reply_info(message, user_data)
        elif message_text in glossary.ENTER_WEIGHT_COMMANDS:
            await reply_enter_weight(message, user_data)
        elif message_text in glossary.SHOW_MENU_COMMANDS:
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
    text = glossary.INFO

    await bot.send_message(message.chat.id, text,
                           reply_markup=DEFAULT_MARKUP,
                           parse_mode="HTML",
                           disable_web_page_preview=True)
    user_data['conversation_state'] = ConversationState.init


async def reply_start(message: types.Message, user_data: dict):
    text = glossary.HELLO
    text += glossary.COMMAND_LIST

    await bot.send_message(message.chat.id, text, reply_markup=DEFAULT_MARKUP, parse_mode="HTML")
    user_data['conversation_state'] = ConversationState.init


async def reply_enter_weight(message: types.Message, user_data):
    text = glossary.HOW_MUCH_DO_YOU_WEIGH
    await bot.send_message(message.chat.id, text, parse_mode="HTML")
    user_data['conversation_state'] = ConversationState.awaiting_body_weight


def text_deficit_maintenance_surplus(speed_week_kg: Optional[float], mean_mass: float) -> str:
    text = ""
    if speed_week_kg is not None:
        maintenance_threshold = mean_mass * src.config.MAINTENANCE_THRESHOLD
        if abs(speed_week_kg) < maintenance_threshold:
            text += glossary.YOU_ARE_MAINTAINING
        else:
            if speed_week_kg > 0:
                text += glossary.YOU_ARE_SURPLUS
            else:
                text += glossary.YOU_ARE_DEFICIT

        if speed_week_kg > 0:
            text += glossary.YOU_ARE_GAINING_TEMPLATE % speed_week_kg
        elif speed_week_kg <= 0:
            text += glossary.YOU_ARE_LOSING_TEMPLATE % abs(speed_week_kg)

        if abs(speed_week_kg) < maintenance_threshold:
            text += glossary.WHICH_IS_TOO_SLOW

    return text


async def reply_body_weight(message: types.Message, user_data):
    try:
        body_weight = float(message.text.strip())
        if not (0 < body_weight < src.config.MAX_BODY_WEIGHT):
            raise ValueError
    except ValueError:
        await bot.reply_to(message, glossary.PLEASE_ENTER_VALID_POSITIVE_NUMBER)
        return

    await add_record_now(message.chat.id, body_weight)
    img_path, speed_week_kg, mean_mass = await plot_user_data(message.chat.id, only_two_weeks=True)
    with open(img_path, 'rb') as img_file_object:
        text = f"{glossary.SUCCESSFULLY_ADDED_NEW_ENTRY}\n" \
               f"<b>{datetime.now().strftime(date_format)} - {body_weight} kg</b>\n"
        text += text_deficit_maintenance_surplus(speed_week_kg, mean_mass)

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
    img_path, speed_week_kg, mean_mass = await plot_user_data(message.chat.id, only_two_weeks=True)
    with open(img_path, 'rb') as img_file_object:
        text = glossary.HERE_PLOT_LAST_TWO_WEEKS
        text += text_deficit_maintenance_surplus(speed_week_kg, mean_mass)

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
    img_path, speed_week_kg, mean_mass = await plot_user_data(message.chat.id, only_two_weeks=False)
    with open(img_path, 'rb') as img_file_object:
        text = glossary.HERE_PLOT_OVERALL_PROGRESS
        text += text_deficit_maintenance_surplus(speed_week_kg, mean_mass)

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
        text = glossary.NO_DATA_TO_DOWNLOAD_YET
        await bot.reply_to(message, text, reply_markup=DEFAULT_MARKUP)
    else:
        text = glossary.HERE_ALL_YOUR_DATA
        text += glossary.YOU_CAN_ANALYZE_OR_BACKUP
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
    text = glossary.REPLY_UPLOAD
    await bot.reply_to(message, text)
    user_data['conversation_state'] = ConversationState.awaiting_csv_table


async def reply_csv_table(message: types.Message, user_data: dict):
    document = message.document
    if document is None:
        await bot.reply_to(message, glossary.NO_VALID_DOCUMENT)
        return

    file_id = document.file_id
    file_size = document.file_size
    if file_size > src.config.MAX_FILE_SIZE:
        await bot.reply_to(message, glossary.FILE_TOO_BIG)
        return

    file_info = await bot.get_file(file_id)
    file_url = 'https://api.telegram.org/file/bot{0}/{1}'.format(src.config.TELEGRAM_TOKEN, file_info.file_path)

    try:
        await user_data_from_csv_url(message.chat.id, file_url, src.config.MAX_BODY_WEIGHT)
    except CSVParsingError:
        await bot.reply_to(message, glossary.FILE_INVALID)
        return
    except Exception as exception:
        await bot.reply_to(message, glossary.FILE_UNEXPECTED_ERROR)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.critical("Unexpected error while processing CSV file [%s:%d]: %s: %s" % (fname, exc_tb.tb_lineno, type(exception).__name__,
                                                              exception))

        return

    img_path, speed_week_kg, mean_mass = await plot_user_data(message.chat.id, only_two_weeks=False)
    with open(img_path, 'rb') as img_file_object:
        text = glossary.DATA_UPLOADED_SUCCESSFULLY
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
    text = glossary.REPLY_ERASE
    await bot.reply_to(message, text, parse_mode='HTML')
    user_data['conversation_state'] = ConversationState.awaiting_erase_confirmation


async def reply_erase_confirmation(message, user_data: dict):
    if message.text.strip().lower() != glossary.CONFIRMATION_WORD:
        text = glossary.CANCEL_DELETE
        await bot.reply_to(message, text, reply_markup=DEFAULT_MARKUP)
        user_data['conversation_state'] = ConversationState.init
        return

    csv_file_path = await user_data_to_csv(message.chat.id)
    await delete_user_data(message.chat.id)

    file_size = os.path.getsize(csv_file_path)
    if file_size == 0:
        text = glossary.NO_DATA_YET
        await bot.reply_to(message, text, reply_markup=DEFAULT_MARKUP)
        user_data['conversation_state'] = ConversationState.init
        return

    text = glossary.ERASE_COMPLETE

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
    text = glossary.UNEXPECTED_DOCUMENT
    await bot.reply_to(message, text, reply_markup=DEFAULT_MARKUP)
    user_data['conversation_state'] = ConversationState.init

asyncio.run(bot.polling(non_stop=True))
