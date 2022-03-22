import logging
import requests
import os
import time
import sys
import json
import http

import telegram
import dotenv

from exceptions import (
    CanNotConnect, EmptyListError, JsonError, HTTPStatusError, CanNotSendMsg
)

dotenv.load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

send_errors = []


def send_message(bot, message):
    """Отправляем сообщение о статусе или ошибках в чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Сообщение отправлено')
    except telegram.TelegramError as error:
        if str(CanNotSendMsg(error)) not in send_errors:
            send_errors.append(str(CanNotSendMsg(error)))
        raise CanNotSendMsg(error)


def get_api_answer(current_timestamp):
    """Делаем запрос на сервер."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except requests.exceptions.RequestException as error:
        raise CanNotConnect(error)
    if homework_statuses.status_code != http.HTTPStatus.OK:
        raise HTTPStatusError(homework_statuses.status_code)
    try:
        homework = homework_statuses.json()
    except json.decoder.JSONDecodeError:
        raise JsonError
    return homework


def check_response(response):
    """Получаем из данных с полученных информацию о ДЗ."""
    if type(response) is not dict:
        raise TypeError(
            'Получен ошибочный тип данных с сревера (необходим словарь)'
        )
    if not len(response):
        raise EmptyListError
    homeworks = response.get('homeworks')
    if type(homeworks) is not list:
        raise TypeError(
            'Получен ошибочный тип данных с сревера (необходим список)'
        )
    return homeworks


def parse_status(homework):
    """получаем информацию о статусе и наименовании работы."""
    if 'homework_name' not in homework:
        raise KeyError('В полученном ответе нет информации о названии работы')
    if 'status' not in homework:
        raise KeyError('В полученном ответе нет информации о статусе')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(
            'В полученном ответе указан не изаестный тип статуса'
        )
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяем наличие необходимых токенов."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    for key, value in tokens.items():
        if not value:
            logger.critical(f'Отутствует {key}')
            return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = (int(time.time()) - RETRY_TIME)
    message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks_list = check_response(response)
            if homeworks_list:
                status = parse_status(homeworks_list[0])
                if status and status != message:
                    send_message(bot, status)
                    message = status
            else:
                logger.debug('Сатус не изменился')
        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
            if f'{error}' not in send_errors:
                error_message = f'Сбой в работе программы: {error}'
                if error_message != message:
                    send_message(bot, error_message)
                    message = error_message
                    time.sleep(RETRY_TIME)
            time.sleep(RETRY_TIME)
        else:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
