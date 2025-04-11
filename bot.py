import telebot
import json
from telebot.types import WebAppInfo, ReplyKeyboardMarkup, Message

TOKEN = '7574772435:AAFjhtjv0CUYyE0rgRuo40FRVOLYN4Zm2QM'
bot = telebot.TeleBot(TOKEN)

user_media = {}
user_stage = {}

@bot.message_handler(commands=['start'])
def start(msg: Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(telebot.types.KeyboardButton(
        text="Открыть магазин",
        web_app=WebAppInfo(url="https://timeluxco-webapp.kirillpiter07.workers.dev/")
    ))
    bot.send_message(msg.chat.id, "Добро пожаловать! Открыть WebApp:", reply_markup=kb)

@bot.message_handler(content_types=['photo', 'video'])
def handle_media(msg: Message):
    user_id = msg.from_user.id
    media = user_media.setdefault(user_id, [])
    if msg.content_type == 'photo':
        file_id = msg.photo[-1].file_id
        media.append({'type': 'photo', 'file_id': file_id})
    elif msg.content_type == 'video':
        media.append({'type': 'video', 'file_id': msg.video.file_id})
    
    if len(media) >= 10:
        bot.send_message(msg.chat.id, "Принято 10 файлов. Теперь отправь описание по шаблону:")
        request_description(msg)
    else:
        bot.send_message(msg.chat.id, f"Файл получен ({len(media)}/10). Можно ещё отправить.")

@bot.message_handler(func=lambda m: user_stage.get(m.from_user.id) == 'awaiting_description')
def handle_description(msg: Message):
    user_id = msg.from_user.id
    text = msg.text.strip()
    parts = text.split('\n')
    if len(parts) < 7:
        bot.send_message(msg.chat.id, "Недостаточно строк. Отправь описание по шаблону.")
        return

    item = {
        "id": generate_id(),
        "title": parts[0].split(":", 1)[-1].strip(),
        "price": int(parts[1].split(":", 1)[-1].strip()),
        "oldPrice": int(parts[2].split(":", 1)[-1].strip()),
        "article": parts[3].split(":", 1)[-1].strip(),
        "description": parts[4].split(":", 1)[-1].strip(),
        "sizes": [s.strip() for s in parts[5].split(":", 1)[-1].split(";")],
        "note": parts[6].split(":", 1)[-1].strip(),
        "images": [{"type": m['type'], "url": f"https://t.me/timeluxcobot/{m['file_id']}"} for m in user_media.get(user_id, [])],
        "visible": True,
        "isNew": True,
        "isOnSale": False
    }

    save_product(item)
    bot.send_message(msg.chat.id, f"✅ Товар добавлен: {item['title']}")
    user_media.pop(user_id, None)
    user_stage.pop(user_id, None)

@bot.message_handler(func=lambda m: m.text.lower().startswith("добавить товар"))
def begin_upload(msg: Message):
    user_media[msg.from_user.id] = []
    user_stage[msg.from_user.id] = 'awaiting_description'
    bot.send_message(msg.chat.id, "Отправь до 10 фото/видео товара.")

def request_description(msg: Message):
    user_stage[msg.from_user.id] = 'awaiting_description'
    bot.send_message(msg.chat.id, "Отправь описание по шаблону:\n\nНазвание:\nЦена:\nЦена до скидки:\nАртикул:\nХарактеристики:\nРазмеры: (через ;)\nДополнительно:")

def save_product(item):
    path = "products.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = []

    data.append(item)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_id():
    path = "products.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return 1
    return max((item.get("id", 0) for item in data), default=0) + 1

print("Бот запущен.")
bot.polling()
