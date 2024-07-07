import logging
from telebot import TeleBot
import os
import time
from dotenv import load_dotenv
import requests
import calendar
from requests import RequestException

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
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
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.critical('Проверьте наличие всех переменных окружения.')
        raise SystemExit


def send_message(bot, message):
    """Отправка сообщения ботом."""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    logging.debug('Сообщение отправлено.')


def get_api_answer(timestamp):
    """Получение ответа от API ЯП."""
    try:
        response = requests.get(ENDPOINT, headers=HEADERS,
                                params={'from_date': timestamp})
    except RequestException:
        pass
    if response.status_code != 200:
        if response.status_code == 400:
            message = response.json().get('error').get('error')
        elif response.status_code == 401:
            message = response.json().get('message')
        else:
            message = f'При отправке запроса возникла ошибка с кодом' \
                f' {response.status_code}. Причина: {response.reason}'
        raise RequestException(message)
    else:
        return response.json()


def check_response(response):
    """Проверка ответа."""
    try:
        response.get('homeworks')
    except Exception:
        pass
    if type(response) is not dict:
        raise TypeError('Response is not dict or empty.')
    elif type(response.get('homeworks')) is not list:
        raise TypeError('Homeworks is not list.')
    elif len(response.get('homeworks')) != 0:
        return True
    else:
        return False


def parse_status(homework):
    """Проверка статуса."""
    if homework.get(
        'status') in HOMEWORK_VERDICTS and homework.get(
            'homework_name'):
        verdict = HOMEWORK_VERDICTS[homework.get('status')]
        homework_name = homework.get('homework_name')
        message = f'Изменился статус проверки работы "{homework_name}".'\
            f'{verdict}'
        return message
    else:
        raise Exception('Problems in homework')


def get_start_time():
    """Первый запрос после запуска бота."""
    response = get_api_answer(0)
    if check_response(response):
        date_updated = response.get('homeworks')[0].get('date_updated')
        last_status_date = time.strptime(date_updated,
                                         '%Y-%m-%dT%H:%M:%S%z')
        start_time = calendar.timegm(last_status_date) + 1
        last_project_name = response.get('homeworks')[0].get('homework_name')
        last_project_status = HOMEWORK_VERDICTS[response.get(
            'homeworks')[0].get('status')]
        message = f'Бот запущен. Статус последнего проекта:'\
            f'{last_project_name} от {date_updated} - {last_project_status}.'
    else:
        start_time = int(time.time() - RETRY_PERIOD)
        message = '''Бот запущен. Список домашнего задания пока пуст.
        Отправленному проекту ещё не присвоен статус.'''
    return start_time, message


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    try:
        timestamp, message = get_start_time()
        send_message(bot, message)
    except Exception as error:
        logging.error(error)

    while True:
        time.sleep(RETRY_PERIOD)
        try:
            response = get_api_answer(timestamp)
            timestamp = int(response.get('current_date'))
            if check_response(response):
                homework = response.get('homeworks')[0]
                message = parse_status(homework)
            else:
                message = 'Отправленному проекту ещё не присвоен статус.'
            send_message(bot, message)
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')


if __name__ == '__main__':
    main()
