import logging
import os
import time
import requests
import telegram

from dotenv import load_dotenv
from http import HTTPStatus
from my_exceptions import NoHTTPResponseError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s, %(lineno)d'
)


def check_tokens():
    """Проверка доступности переменных окружения.

    Если отсутствует хоть одна переменная,
    то прекращаем выполнение всей программы.
    """
    values = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ]
    for value in values:
        if value is None:
            logging.critical('Отсутствуют обязательные переменные окружения')
            exit()


def send_message(bot, message):
    """Шлем сообщение в чат."""
    try:
        logging.debug(f'Отправленно сообщение {message}')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logging.error(error)


def get_api_answer(timestamp):
    """Делаем запрос к эндпоинту API-сервиса.

    В качестве параметра передаем временную метку TIMEPOINT.
    Ответ API, приводим из формата JSON к типам данных Python.
    """
    timestamp = int(time.time())
    time_point = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params=time_point
                                )
    except Exception as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')
    if response.status_code != HTTPStatus.OK:
        raise NoHTTPResponseError(response)
    return response.json()


def check_response(response):
    """Проверяем ответ API.

    1. Ответ от апи существует
    2. Ответ от апи - словарь
    3. Ключ 'homeworks' есть в словаре
    4. Значение ключа 'homeworks' - список
    """
    if not response:
        text = 'Нет ответа от API.'
        logging.error(text)
        raise KeyError(text)
    if not isinstance(response, dict):
        text = 'Ответ от API не является словарем.'
        logging.error(text)
        raise TypeError(text)
    if 'homeworks' not in response:
        text = 'Запрошенный ключ отсутствует в ответе.'
        logging.error(text)
        raise KeyError(text)
    if not isinstance(response.get('homeworks'), list):
        text = 'Значение ключа не является списком'
        logging.error(text)
        raise TypeError(text)
    return response['homeworks']


def parse_status(homework):
    """Узнаем статус домашней работы.

    В качестве параметра передаем только один элемент из списка
    домашних работ.
    В случае успеха, функция возвращает подготовленную для отправки в Telegram
    строку из словаря HOMEWORK_VERDICT.
    """
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    for hw_status, verdict in HOMEWORK_VERDICTS.items():
        if status not in HOMEWORK_VERDICTS:
            raise Exception('API домашки недокументированный статус.')
        if 'homework_name' not in homework.keys():
            raise Exception('В ответе API домашки нет ключа `homework_name`!')
        if hw_status == status:
            return (f'Изменился статус проверки '
                    f'работы "{homework_name}". {verdict}')


def main():
    """Основная логика работы бота.

    1) Сделать запрос к API.
    2) Проверить ответ.
    3) Если есть обновления — получить статус работы из обновления
    и отправить сообщение в Telegram.
    4) Подождать некоторое время и вернуться в пункт 1.
    """
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                if homework:
                    message = parse_status(homework)
                    send_message(bot, message)
                    logging.debug(f'Отправленно сообщение из бота: {message}')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logging.debug(f'Отправленно сообщение о сбое {message}')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
