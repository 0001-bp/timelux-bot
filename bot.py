
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

class ProductForm(StatesGroup):
    waiting_for_media = State()
    waiting_for_text = State()

@dp.message_handler(commands="start")
async def start(message: types.Message):
    await message.answer("Отправьте до 10 фото или видео товара.")

@dp.message_handler(content_types=types.ContentType.ANY, state=None)
async def receive_media(message: types.Message, state: FSMContext):
    if message.content_type not in [types.ContentType.PHOTO, types.ContentType.VIDEO]:
        await message.answer("Пожалуйста, отправьте до 10 фото или видео товара.")
        return
    await state.update_data(media=[message])
    await ProductForm.waiting_for_media.set()
    await message.answer("Принял ✅
Теперь отправьте описание товара в формате:

Название:
Цена:
Цена до скидки:
Артикул:
Характеристики:
Размеры (через ;)")

@dp.message_handler(state=ProductForm.waiting_for_media, content_types=types.ContentType.ANY)
async def collect_more_media(message: types.Message, state: FSMContext):
    data = await state.get_data()
    media = data.get("media", [])
    if message.content_type in [types.ContentType.PHOTO, types.ContentType.VIDEO]:
        media.append(message)
        if len(media) >= 10:
            await state.update_data(media=media)
            await ProductForm.waiting_for_text.set()
            await message.answer("Прием медиа завершён ✅
Теперь отправьте описание товара.")
        else:
            await state.update_data(media=media)
            await message.answer(f"Файл {len(media)}/10 принят. Жду остальные...")
    else:
        await message.answer("Теперь отправьте описание товара.")

@dp.message_handler(state=ProductForm.waiting_for_text)
async def receive_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    media = data.get("media", [])
    await message.answer("🛒 Товар добавлен. Спасибо!")
    # Здесь можно подключить сохранение в базу, пересылку в WebApp и т.д.
    await state.finish()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
