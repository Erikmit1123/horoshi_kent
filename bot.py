import telebot
from telebot import types
import random
import string
import phonenumbers
from phonenumbers import geocoder, timezone, carrier
from phonenumbers.phonenumberutil import NumberParseException
import logging
import csv  # Импортируем модуль csv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '8034977004:AAE8RPdTPqMhe0bQgV8rNUKqcplO-BCymd8'  # Замените на токен вашего бота
bot = telebot.TeleBot(TOKEN)

user_phones = {}
user_states = {}
EXCEL_FILE_PATH = '/home/Erikmit/base.csv'  # Указываем путь к CSV-файлу

def search_in_csv(file_path, search_query, search_column_name):
    """
    Ищет запись в CSV-файле по заданному значению в указанном столбце.

    Args:
        file_path (str): Путь к файлу CSV.
        search_query (str): Значение для поиска.
        search_column_name (str): Название столбца, в котором нужно искать.

    Returns:
        dict or None: Словарь с найденной информацией (где ключи - заголовки столбцов),
                     или None, если ничего не найдено.
    """
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            if reader.fieldnames:
                try:
                    search_column_index = reader.fieldnames.index(search_column_name)
                except ValueError:
                    return f"Ошибка: Столбец '{search_column_name}' не найден в файле."

                for row in reader:
                    if row[search_column_name] is not None and row[search_column_name] == search_query:
                        return row
            else:
                return "Ошибка: Файл CSV пустой или не имеет заголовков."
        return None
    except FileNotFoundError:
        return f"Ошибка: Файл '{file_path}' не найден."
    except Exception as e:
        return f"Произошла ошибка при чтении CSV: {e}"

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    item1 = types.KeyboardButton("Поиск")
    item2 = types.KeyboardButton("Информация о пользователе")
    item3 = types.KeyboardButton("Генерация пароля")
    item4 = types.KeyboardButton("Поиск по базе") # Общее название для поиска по базе
    markup.add(item1, item2, item3, item4)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Поиск")
def search_menu_handler(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    item1 = types.KeyboardButton("Поиск по нику в интернете") # Более точное название
    item2 = types.KeyboardButton("Поиск по номеру телефона")
    markup.add(item1, item2)
    bot.send_message(message.chat.id, "Выберите тип поиска:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Информация о пользователе")
def send_info_handler(message):
    user_id = message.chat.id
    first_name = message.chat.first_name
    last_name = message.chat.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = message.chat.username or "не указан"
    language_code = message.from_user.language_code

    bot.send_message(message.chat.id, f"Ваш ID: {user_id}\nВаше имя: {full_name}\nВаш username: @{username}\nЯзык: {language_code}")

@bot.message_handler(func=lambda message: message.text == "Поиск по нику в интернете") # Обновленный обработчик
def nick_search_internet_start_handler(message):
    bot.send_message(message.chat.id, "Введите ник для поиска в интернете:")
    user_states[message.chat.id] = "nick_search_internet"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "nick_search_internet")
def nick_search_internet_process(message):
    user = message.text
    chat_id = message.chat.id
    user_states.pop(chat_id, None)

    links = {
        "Telegram": "https://t.me/" + user,
        "Вконтакте": "https://vk.com/" + user,
        "Одноклассники": "https://ok.ru/" + user,
        "Github": "https://github.com/" + user,
        "Yandex": "https://yandex.ru/search/?text=" + user,
        "Instagram": "https://www.instagram.com/" + user,
        "TikTok": "https://www.tiktok.com/@" + user,
        "Twitter": "https://twitter.com/" + user,
        "Facebook": "https://www.facebook.com/" + user,
        "YouTube": "https://www.youtube.com/@" + user,
        "Twitch": "https://www.twitch.tv/" + user,
        "Roblox": "https://www.roblox.com/" + user,
        "Discord": "https://discord.com/channels/@me/" + user,
        "Steam": "https://steamcommunity.com/id/" + user,
        "Spotify": "https://open.spotify.com/search/" + user,
    }

    message_text = "Проверьте эти ссылки:\n"
    for site, link in links.items():
        message_text += f"---------------\n{site}: {link}\n"
    message_text += "---------------\n"

    bot.send_message(chat_id, message_text)

# Обработчик для кнопки поиска по номеру телефона
@bot.message_handler(func=lambda message: message.text == "Поиск по номеру телефона")
def phone_search_start_handler(message):
    bot.send_message(message.chat.id, "Введите номер телефона для поиска:")
    user_states[message.chat.id] = "phone_search"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "phone_search")
def phone_search_process(message):
    phone = message.text
    chat_id = message.chat.id
    user_states.pop(chat_id, None)

    def phoneinfo(phone):
        try:
            parsed_phone = phonenumbers.parse(phone, None)
            if not phonenumbers.is_valid_number(parsed_phone):
                return "Ошибка: Недействительный номер телефона"

            country = geocoder.description_for_number(parsed_phone, "en")
            region = geocoder.description_for_number(parsed_phone, "ru")
            formatted_number = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            is_valid = phonenumbers.is_valid_number(parsed_phone)
            is_possible = phonenumbers.is_possible_number(parsed_phone)
            timezona = timezone.time_zones_for_number(parsed_phone)

            try:
                carrier_info = carrier.name_for_number(parsed_phone, "en")
            except NumberParseException:
                carrier_info = "Информация об операторе недоступна"

            print_phone_info = f"""
[+] Номер телефона: {formatted_number}
[+] Страна: {country}
[+] Регион: {region}
[+] Оператор: {carrier_info}
[+] Активен: {is_possible}
[+] Валид: {is_valid}
[+] Таймзона: {timezona}
[+] Telegram: https://t.me/{phone}
[+] Whatsapp: https://wa.me/{phone}
[+] Viber: https://viber.click/{phone}
"""
            return print_phone_info

        except Exception as e:
            return f"Ошибка: {str(e)}"

    result = phoneinfo(phone)
    bot.send_message(chat_id, result)

@bot.message_handler(func=lambda message: message.text == "Генерация пароля")
def password_generation_start_handler(message):
    bot.send_message(message.chat.id, "Введите длину пароля:")
    user_states[message.chat.id] = ("password_length",)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, ("",))[0] == "password_length")
def password_length_process(message):
    try:
        password_length = int(message.text)
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        item1 = types.KeyboardButton("Low")
        item2 = types.KeyboardButton("Medium")
        item3 = types.KeyboardButton("High")
        markup.add(item1, item2, item3)
        bot.send_message(message.chat.id, "Выберите сложность:", reply_markup=markup)
        user_states[message.chat.id] = ("password_complexity", password_length)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректную длину пароля. Например: 8, 12, 16 и т.д.")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, ("",))[0] == "password_complexity")
def password_complexity_select(message):
    complexity_text = message.text
    chat_id = message.chat.id

    state = user_states.get(chat_id)
    if not state or len(state) < 2:
        bot.send_message(chat_id, "Сначала укажите длину пароля.")
        return

    password_length = state[1]
    complexity = None
    if complexity_text == 'Low':
        complexity = 'low'
    elif complexity_text == 'Medium':
        complexity = 'medium'
    elif complexity_text == 'High':
        complexity = 'high'

    if complexity:
        def generate_password(length, complexity):
            if complexity == 'low':
                characters = string.ascii_lowercase + string.digits
            elif complexity == 'medium':
                characters = string.ascii_letters + string.digits
            elif complexity == 'high':
                characters = string.ascii_letters + string.digits + string.punctuation
            return ''.join(random.choice(characters) for _ in range(length))

        password = generate_password(password_length, complexity)
        bot.send_message(chat_id, f"Ваш сгенерированный пароль: {password}", reply_markup=types.ReplyKeyboardRemove())
        user_states.pop(chat_id, None)
    else:
        bot.send_message(chat_id, "Пожалуйста, выберите сложность из предложенных кнопок.")

@bot.message_handler(func=lambda message: message.text == "Поиск по базе") # Обновленное название кнопки
def excel_search_start_handler(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    item1 = types.KeyboardButton("Поиск по нику") # Кнопка поиска по нику в базе
    item2 = types.KeyboardButton("Поиск по ID")
    item3 = types.KeyboardButton("Поиск по Telegram ID")
    back_button = types.KeyboardButton("Назад")
    markup.add(item1, item2, item3, back_button)
    bot.send_message(message.chat.id, "Выберите тип поиска в базе:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Поиск по нику") # Обработчик поиска по нику в базе
def excel_nick_search_handler(message):
    bot.send_message(message.chat.id, "Введите ник для поиска в базе данных:")
    user_states[message.chat.id] = "excel_nick_search_query"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "excel_nick_search_query")
def excel_nick_search_process(message):
    search_query = message.text
    chat_id = message.chat.id
    user_states.pop(chat_id, None)

    result = search_in_csv(EXCEL_FILE_PATH, search_query, 'ник') # Предполагаем, что столбец называется 'ник'

    if isinstance(result, str):
        bot.send_message(chat_id, result)
    elif result:
        response_text = "Найдена следующая информация по нику:\n"
        for key, value in result.items():
            response_text += f"{key}: {value}\n"
        bot.send_message(chat_id, response_text)
    else:
        bot.send_message(chat_id, f"По нику '{search_query}' ничего не найдено в базе.")

@bot.message_handler(func=lambda message: message.text == "Поиск по ID")
def excel_id_search_handler(message):
    bot.send_message(message.chat.id, "Введите ID для поиска в базе данных:")
    user_states[message.chat.id] = "excel_id_search_query"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "excel_id_search_query")
def excel_id_search_process(message):
    search_query = message.text
    chat_id = message.chat.id
    user_states.pop(chat_id, None)

    result = search_in_csv(EXCEL_FILE_PATH, search_query, 'id') # Ищем в столбце 'id'

    if isinstance(result, str):
        bot.send_message(chat_id, result)
    elif result:
        response_text = "Найдена следующая информация по ID:\n"
        for key, value in result.items():
            response_text += f"{key}: {value}\n"
        bot.send_message(chat_id, f"Найдена следующая информация по ID:\n{', '.join([f'{k}: {v}' for k, v in result.items()])}")
    else:
        bot.send_message(chat_id, f"По ID '{search_query}' ничего не найдено в базе.")

@bot.message_handler(func=lambda message: message.text == "Поиск по Telegram ID")
def excel_telegram_id_search_handler(message):
    bot.send_message(message.chat.id, "Введите Telegram ID для поиска в базе данных:")
    user_states[message.chat.id] = "excel_telegram_id_search_query"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "excel_telegram_id_search_query")
def excel_telegram_id_search_process(message):
    search_query = message.text
    chat_id = message.chat.id
    user_states.pop(chat_id, None)

    result = search_in_csv(EXCEL_FILE_PATH, search_query, 'Telegram ID') # Ищем в столбце 'Telegram ID'

    if isinstance(result, str):
        bot.send_message(chat_id, result)
    elif result:
        response_text = "Найдена следующая информация по Telegram ID:\n"
        for key, value in result.items():
            response_text += f"{key}: {value}\n"
        bot.send_message(chat_id, f"Найдена следующая информация по Telegram ID:\n{', '.join([f'{k}: {v}' for k, v in result.items()])}")
    else:
        bot.send_message(chat_id, f"По Telegram ID '{search_query}' ничего не найдено в базе.")

@bot.message_handler(func=lambda message: message.text == "Назад", content_types=['text'])
def back_to_main_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    item1 = types.KeyboardButton("Поиск")
    item2 = types.KeyboardButton("Информация о пользователе")
    item3 = types.KeyboardButton("Генерация пароля")
    item4 = types.KeyboardButton("Поиск по базе")
    markup.add(item1, item2, item3, item4)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

bot.polling()