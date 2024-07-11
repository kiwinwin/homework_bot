import logging
from http import HTTPStatus
from telebot import TeleBot
import os
import time
from dotenv import load_dotenv
import requests
import calendar
from requests import RequestException
from exceptions import (NoEnvVarError,
                        GetApiError,
                        ResponseCheckingError,
                        StatusParsingError,
                        MessageSendingError,
                        GetStartTimeError,
                        RepeatedMessagesError)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


logging.basicConfig(
    format='''%(asctime)s - [%(levelname)s] - %(funcName)s -
    %(lineno)d - %(message)s''',
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    encoding='utf-8',
)


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка наличия токенов."""
    env_variables = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
                     'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
                     'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
                     }
    no_variables = [name for name, value in env_variables.items() if not value]
    if no_variables:
        no_variables = ', '.join(no_variables)
        raise NoEnvVarError(
            f'Проверьте наличие {no_variables} в переменных окружения.')


def send_message(bot, message):
    """Отправка сообщения ботом."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug('Сообщение отправлено.')
    except Exception as error:
        raise MessageSendingError(error)


def repeated_messages(bot, message, last_message):
    """Проверка отправки повторных сообщений."""
    try:
        if last_message != message:
            send_message(bot, message)
        else:
            logging.debug(message)
        return message
    except Exception as error:
        raise RepeatedMessagesError(error)


def get_api_answer(timestamp):
    """Получение ответа от API ЯП."""
    try:
        response = requests.get(ENDPOINT, headers=HEADERS,
                                params={'from_date': timestamp})
    except RequestException as error:
        raise GetApiError(error)
    if response.status_code != HTTPStatus.OK:
        message = f'При отправке запроса возникла ошибка с кодом' \
            f' {response.status_code}. Причина: {response.reason}'
        raise GetApiError(message)
    else:
        logging.debug('Ответ API получен.')
        return response.json()


def check_response(response):
    """Проверка ответа."""
    if type(response) is not dict:
        raise TypeError(ResponseCheckingError('Wrong API response.'))
    try:
        response.get('homeworks')
    except Exception as error:
        raise ResponseCheckingError(error)
    if type(response.get('homeworks')) is not list:
        raise TypeError(ResponseCheckingError('Wrong homeworks.'))
    elif len(response.get('homeworks')) != 0:
        return True
    else:
        return False


def parse_status(homework):
    """Проверка статуса."""
    try:
        homework.get('status')
        verdict = HOMEWORK_VERDICTS[homework.get('status')]
    except Exception as error:
        raise StatusParsingError(error, ': status')
    try:
        homework.get('homework_name')
        homework_name = homework.get('homework_name')
    except Exception as error:
        raise StatusParsingError(error, ': homework_name')
    if not homework_name:
        raise StatusParsingError(': homework_name')
    message = f'Изменился статус проверки работы "{homework_name}".'\
        f'{verdict}'
    return message


def get_start_time():
    """Первый запрос после запуска бота."""
    try:
        response = get_api_answer(0)
        if check_response(response):
            date_updated = response.get('homeworks')[0].get('date_updated')
            last_status_date = time.strptime(date_updated,
                                             '%Y-%m-%dT%H:%M:%S%z')
            start_time = calendar.timegm(last_status_date) + 1
            last_project_name = response.get(
                'homeworks')[0].get('homework_name')
            last_project_status = HOMEWORK_VERDICTS[response.get(
                'homeworks')[0].get('status')]
            message = f'Бот запущен. Статус последнего проекта:'\
                f'{last_project_name} от {date_updated}:{last_project_status}.'
        else:
            start_time = int(time.time() - RETRY_PERIOD)
            message = '''Бот запущен. Список домашнего задания пока пуст.
            Отправленному проекту ещё не присвоен статус.'''
        return start_time, message
    except Exception as error:
        raise GetStartTimeError(error)


def main():
    """Основная логика работы бота."""
    try:
        check_tokens()
        bot = TeleBot(token=TELEGRAM_TOKEN)
        timestamp, message = get_start_time()
        last_message = repeated_messages(bot, message, None)
    except NoEnvVarError as error:
        logging.critical(error)
        raise SystemExit
    except Exception as error:
        logging.error(error)

    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = int(response.get('current_date'))
            if check_response(response):
                homework = response.get('homeworks')[0]
                message = parse_status(homework)
            else:
                message = 'Отправленному проекту ещё не присвоен статус.'
            last_message = repeated_messages(bot, message, last_message)
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
