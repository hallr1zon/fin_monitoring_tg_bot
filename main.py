import asyncio
import logging
import re
import sys
from os import getenv

import uvloop
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from dotenv import load_dotenv

from app import constants as const
from app.actions import ACTIONS
from app.models.models import User, Transaction
from app.keyboards import start_keyboard, cancel_keyboard

load_dotenv()

TOKEN = getenv("BOT_TOKEN")


class FormRecord(StatesGroup):
    amount = State()
    category = State()
    description = State()


class NewMonthlyLimit(StatesGroup):
    amount = State()


dp = Dispatcher()
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """ /start command """
    await User.start_command(message)


@dp.message(F.text.casefold() == "відміна")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "🤝Відміна успішна",
            reply_markup=start_keyboard,
        )
        return

    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        "🤝Відміна успішна",
        reply_markup=start_keyboard,
    )


@dp.message(F.text.lower() == ACTIONS[const.ADD_RECORD].lower())
async def add_new_record(message: types.Message, state: FSMContext):
    await message.answer(
        "Скільки коштів ви витратили?",
        reply_markup=cancel_keyboard
    )
    await state.set_state(FormRecord.amount)


@dp.message(FormRecord.amount)
async def process_amount(message: Message, state: FSMContext) -> None:
    await Transaction.prepare_amount(message, state)


@dp.message(FormRecord.category)
async def process_category(message: Message, state: FSMContext) -> None:
    await Transaction.prepare_category(message, state)


@dp.message(FormRecord.description)
async def process_description(message: Message, state: FSMContext) -> None:
    await Transaction.add_transaction(message, state)


@dp.message(F.text.lower() == ACTIONS[const.UPDATE_BUDGET].lower())
async def update_budget(message: types.Message):
    buttons = [
        [
            types.InlineKeyboardButton(text="Змінити", callback_data="button_1"),
        ],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    user = await User.get(telegram_id=message.chat.id)
    await message.answer(f"💳Ліміт: {user.monthly_limit} грн", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == 'button_1')
async def process_callback_button1(callback_query: types.CallbackQuery, state):
    await bot.send_message(
        callback_query.message.chat.id,
        text="Введіть нове значення",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(NewMonthlyLimit.amount)


@dp.message(NewMonthlyLimit.amount)
async def process_monthly_amount(message: Message, state: FSMContext) -> None:
    await User.update_monthly_limit(message, state)


@dp.message(F.text.lower() == ACTIONS[const.MONTHLY_COSTS].lower())
async def monthly_costs(message: types.Message):
    buttons = [
        [
            types.InlineKeyboardButton(text="Сьогодні", callback_data="button_2"),
            types.InlineKeyboardButton(text="Місяць", callback_data="button_3"),
        ],
        [
            types.InlineKeyboardButton(text="CSV звіт за місяць", callback_data="button_4"),
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(f"Витрати за", reply_markup=keyboard)

    @dp.callback_query(lambda c: c.data == 'button_2')
    async def process_callback_button1(callback_query: types.CallbackQuery):
        await Transaction.day_report(callback_query.message)

    @dp.callback_query(lambda c: c.data == 'button_3')
    async def process_callback_button1(callback_query: types.CallbackQuery):
        await Transaction.month_report(callback_query.message)

    @dp.callback_query(lambda c: c.data == 'button_4')
    async def process_callback_button1(callback_query: types.CallbackQuery):
        await Transaction.csv_month_report(callback_query.message)


@dp.message(F.text.lower() == ACTIONS[const.MONTHLY_ANALYTICS].lower())
async def monthly_costs(message: types.Message):
    await Transaction.month_analytics(message)


@dp.message(F.text.lower() == ACTIONS[const.ALL_RECORDS].lower())
async def all_records(message: types.Message, state):
    await Transaction.all_records(message, state)


@dp.callback_query(lambda c: re.match(r'record_\d+', c.data))
async def process_callback_button1(callback_query: types.CallbackQuery, state):
    record_id = callback_query.data.split("_")[-1]
    tr = await Transaction.get(id=record_id)

    await tr.delete()
    await callback_query.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await callback_query.bot.answer_callback_query(callback_query.id, "Запис успішно видалено", )


@dp.message(F.text.regexp('.*<-Сторінка'))
async def process_callback_button1(message: types.Message, state):
    pagination_num = message.text.split('<-')[0]
    await Transaction.all_records(message, state, pagination_num=pagination_num, next=False)


@dp.message(F.text.regexp('Сторінка->.*'))
async def process_callback_button1(message: types.Message, state):
    pagination_num = message.text.split('->')[-1]
    await Transaction.all_records(message, state, pagination_num=pagination_num)


async def bot_pulling() -> None:
    await dp.start_polling(bot)


async def db_init() -> None:
    from app.models.models import init
    await init()


async def main() -> None:
    await asyncio.gather(
        bot_pulling(),
        db_init()
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    uvloop.install()
    asyncio.run(main())
