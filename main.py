import telebot
import logging 
import os
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

user_data = {}


# ========== КЛАВИАТУРЫ ==========

def get_budget_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("до 5 млн ₽", callback_data="budget_5"),
        InlineKeyboardButton("5–7 млн ₽", callback_data="budget_7"),
        InlineKeyboardButton("7–10 млн ₽", callback_data="budget_10"),
        InlineKeyboardButton("10–15 млн ₽", callback_data="budget_15"),
        InlineKeyboardButton("15+ млн ₽", callback_data="budget_plus"),
        InlineKeyboardButton("✏️ Ввести свою сумму", callback_data="budget_custom")
    )
    return keyboard


def get_rooms_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for i in range(1, 6):
        buttons.append(InlineKeyboardButton(str(i), callback_data=f"rooms_{i}"))
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton("5+ комнат", callback_data="rooms_5plus"))
    return keyboard


def get_district_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Центральный", callback_data="district_center"),
        InlineKeyboardButton("Дзержинский", callback_data="district_dzer"),
        InlineKeyboardButton("Заельцовский", callback_data="district_zael"),
        InlineKeyboardButton("Калининский", callback_data="district_kalin"),
        InlineKeyboardButton("Кировский", callback_data="district_kirov"),
        InlineKeyboardButton("Ленинский", callback_data="district_lenin"),
        InlineKeyboardButton("Октябрьский", callback_data="district_okt"),
        InlineKeyboardButton("Первомайский", callback_data="district_perv"),
        InlineKeyboardButton("Советский", callback_data="district_sov")
    )
    return keyboard


def get_mortgage_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Да", callback_data="mortgage_yes"),
        InlineKeyboardButton("❌ Нет", callback_data="mortgage_no")
    )
    return keyboard


# ========== ОБРАБОТЧИКИ КОМАНД ==========

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    user_data[user_id] = {}
    
    bot.send_message(
        user_id,
        f"Здравствуйте, {message.from_user.first_name} | Новостройки.\n\n"
        "Я помощник канала «Города»\n"
        "- Мой сервис помогает жителям Новосибирска и других регионов РФ "
        "в подборе самых интересных объектов недвижимости\n\n"
        "- Ответьте на мои вопросы о ваших пожеланиях, и мы сможем подобрать лучший вариант"
    )
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🏠 Квартира для себя", callback_data="interest_self"),
        InlineKeyboardButton("💰 Инвестиционная квартира", callback_data="interest_invest"),
        InlineKeyboardButton("📢 Хочу разместить свой объект", callback_data="interest_sell"),
        InlineKeyboardButton("👀 Просто смотрю", callback_data="interest_watch")
    )
    
    bot.send_message(user_id, "Ответьте, пожалуйста, что вас интересует?", reply_markup=keyboard)


@bot.message_handler(commands=['cancel'])
def handle_cancel(message):
    user_id = message.chat.id
    if user_id in user_data:
        user_data.pop(user_id)
    bot.send_message(user_id, "❌ Опрос отменён. Чтобы начать заново, нажмите /start")


# ========== ОБРАБОТЧИКИ CALLBACK ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('interest_'))
def handle_interest_callback(call):
    user_id = call.message.chat.id
    
    interest_map = {
        'interest_self': 'Квартира для себя',
        'interest_invest': 'Инвестиционная квартира',
        'interest_sell': 'Хочу разместить свой объект',
        'interest_watch': 'Просто смотрю'
    }
    user_data[user_id]['interest'] = interest_map[call.data]
    
    bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=None)
    bot.answer_callback_query(call.id)
    
    bot.send_message(user_id, "💰 Выберите бюджет или укажите свою сумму:", reply_markup=get_budget_keyboard())


@bot.callback_query_handler(func=lambda call: call.data.startswith('budget_'))
def handle_budget_callback(call):
    user_id = call.message.chat.id
    
    budget_map = {
        'budget_5': 'до 5 млн',
        'budget_7': '5–7 млн',
        'budget_10': '7–10 млн',
        'budget_15': '10–15 млн',
        'budget_plus': 'более 15 млн'
    }
    
    if call.data == 'budget_custom':
        bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=None)
        bot.answer_callback_query(call.id)
        msg = bot.send_message(user_id, "✏️ Введите желаемую сумму в рублях (например: 8500000)")
        bot.register_next_step_handler(msg, handle_custom_budget)
        return
    
    user_data[user_id]['budget_limit'] = budget_map.get(call.data, 'не указан')
    
    bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=None)
    bot.answer_callback_query(call.id)
    
    bot.send_message(user_id, "🛏 Сколько комнат вы хотите?", reply_markup=get_rooms_keyboard())


def handle_custom_budget(message):
    user_id = message.chat.id
    try:
        budget = int(message.text.replace(' ', '').replace('₽', ''))
        user_data[user_id]['budget_limit'] = f"{budget:,} ₽".replace(',', ' ')
    except ValueError:
        user_data[user_id]['budget_limit'] = message.text
    bot.send_message(user_id, "🛏 Сколько комнат вы хотите?", reply_markup=get_rooms_keyboard())


@bot.callback_query_handler(func=lambda call: call.data.startswith('rooms_'))
def handle_rooms_callback(call):
    user_id = call.message.chat.id
    
    rooms = call.data.split('_')[1]
    rooms_display = rooms if rooms != '5plus' else '5+'
    user_data[user_id]['rooms'] = rooms_display
    
    bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=None)
    bot.answer_callback_query(call.id)
    
    bot.send_message(user_id, "📍 Выберите предпочтительный район:", reply_markup=get_district_keyboard())


@bot.callback_query_handler(func=lambda call: call.data.startswith('district_'))
def handle_district_callback(call):
    user_id = call.message.chat.id
    
    district_map = {
        'district_center': 'Центральный',
        'district_dzer': 'Дзержинский',
        'district_zael': 'Заельцовский',
        'district_kalin': 'Калининский',
        'district_kirov': 'Кировский',
        'district_lenin': 'Ленинский',
        'district_okt': 'Октябрьский',
        'district_perv': 'Первомайский',
        'district_sov': 'Советский'
    }
    user_data[user_id]['district'] = district_map.get(call.data, 'не указан')
    
    bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=None)
    bot.answer_callback_query(call.id)
    
    bot.send_message(user_id, "🏦 Нужна ли вам ипотека?", reply_markup=get_mortgage_keyboard())


@bot.callback_query_handler(func=lambda call: call.data.startswith('mortgage_'))
def handle_mortgage_callback(call):
    user_id = call.message.chat.id
    
    user_data[user_id]['mortgage'] = 'Да' if call.data == 'mortgage_yes' else 'Нет'
    
    bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=None)
    bot.answer_callback_query(call.id)
    
    msg = bot.send_message(user_id, "👤 Как Вас зовут?")
    bot.register_next_step_handler(msg, handle_name)


def handle_name(message):
    user_id = message.chat.id
    user_data[user_id]['name'] = message.text.strip()
    
    msg = bot.send_message(user_id, "📞 Напишите свой номер телефона в формате 7XXXXXXXXXX")
    bot.register_next_step_handler(msg, handle_phone)


def handle_phone(message):
    user_id = message.chat.id
    phone = message.text.strip()
    
    # Простая проверка номера
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) == 11 and (digits[0] == '7' or digits[0] == '8'):
        user_data[user_id]['phone'] = digits
    else:
        user_data[user_id]['phone'] = phone
    
    answer = (
        "📝 *Новая заявка с канала «Города»*\n\n"
        f"👤 *Имя:* {user_data[user_id].get('name', '—')}\n"
        f"📞 *Телефон:* {user_data[user_id].get('phone', '—')}\n"
        f"🏠 *Интерес:* {user_data[user_id].get('interest', '—')}\n"
        f"💰 *Бюджет:* {user_data[user_id].get('budget_limit', '—')}\n"
        f"🛏 *Комнаты:* {user_data[user_id].get('rooms', '—')}\n"
        f"📍 *Район:* {user_data[user_id].get('district', '—')}\n"
        f"🏦 *Ипотека:* {user_data[user_id].get('mortgage', '—')}\n"
        f"🆔 *User ID:* `{user_id}`"
    )
    
    bot.send_message(ADMIN_CHAT_ID, answer, parse_mode='Markdown')
    
    bot.send_message(
        user_id,
        "✅ *Спасибо!* Ваши данные переданы нашему специалисту.\n"
        "Ожидайте звонка или сообщения в ближайшее время.",
        parse_mode='Markdown'
    )
    
    user_data.pop(user_id, None)


# ========== ЗАПУСК БОТА ==========

if __name__ == '__main__':
    print("🚀 Бот запущен и работает через Long Polling...")
    bot.infinity_polling()
