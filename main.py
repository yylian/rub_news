from urllib3 import PoolManager
from bs4 import BeautifulSoup
from telegram.ext import Updater
from telegram import ParseMode
from markdownify import markdownify as md
from hashlib import sha256
import sys
import time


def main(bot, chat_id):

    html_content = get_html_content()
    raw_entries = get_entries(html_content)
    last_message_hash = get_last_message_hash(bot, chat_id)

    entries = filter_entries(raw_entries, last_message_hash)

    send_messages(entries, bot, chat_id)


def get_telegram_token():

    try:

        token = sys.argv[1]

    except IndexError:

        raise ValueError('No token given')

    return token


def get_html_content():

    manager = PoolManager()
    method = 'GET'
    url = 'http://www.es.rub.de/index.php'

    content = manager.request(method=method, url=url)
    html_content = content.data.decode('latin-1')

    return html_content


def get_entries(html_content):

    entries = []

    soup = BeautifulSoup(html_content, features="html.parser")

    h2_header = soup.find('strong', text="News  Aktuelle Mitteilungen ").parent

    entry = h2_header.findNext('div')

    while entry is not None:

        entries.append(entry)
        entry = entry.findNext('div')

    return entries


def get_last_message_hash(bot, chat_id):

    last_hash = bot.getChat(chat_id=chat_id).description

    return last_hash


def set_last_message_hash(bot, message, chat_id):

    last_message_hash = sha256(message.encode('utf-8')).hexdigest()

    bot.set_chat_description(chat_id, str(last_message_hash))


def filter_entries(raw_entries, last_message_hash):

    entries = []

    for entry in raw_entries:

        entry_is_not_valid = 'align' in entry.attrs and entry.attrs['align'] == 'center'

        if entry_is_not_valid:

            continue

        message = str(entry)

        entries.append(message)

    new_entries = []

    for entry in entries:

        hash_of_current_message = sha256(entry.encode('utf-8')).hexdigest()

        if hash_of_current_message == last_message_hash:

            return new_entries

        new_entries.append(entry)

    return entries


def send_messages(entries, bot, chat_id):

    if not entries:

        return

    last_message = entries[0]

    set_last_message_hash(bot, last_message, chat_id)

    for entry in reversed(entries):

        message = format_message(entry)

        bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN)

        time.sleep(1)


def format_message(message):

    html_tags_to_be_removed = ['h7']

    message = md(message, strip=html_tags_to_be_removed)

    return message


if __name__ == '__main__':

    fallback_id = 145310771
    chat_id = -1001076294841
    token = get_telegram_token()
    bot = Updater(token=token).bot

    try:

        main(bot, chat_id)

    except Exception as exception:

        text = 'RUB - CHAT:\n'
        text += str(exception)
        text += exception.with_traceback()

        bot.send_message(fallback_id, text)
