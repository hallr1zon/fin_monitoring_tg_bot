from aiogram import types
from app import constants as const
from app.actions import ACTIONS

start_kb = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text=ACTIONS[const.ADD_RECORD]),
            types.KeyboardButton(text=ACTIONS[const.UPDATE_BUDGET]),
            types.KeyboardButton(text=ACTIONS[const.MONTHLY_ANALYTICS]),
        ],
        [
            types.KeyboardButton(text=ACTIONS[const.MONTHLY_COSTS]),
            types.KeyboardButton(text=ACTIONS[const.ALL_RECORDS]),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="...",
)

cancel_kb = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text="Відміна"),
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Повернутись до головного меню",
)


def process_pagination_keyboard(pre_number, next_number):
    pagination_keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text=ACTIONS[const.CANCEL]),
                types.KeyboardButton(text=f"{pre_number}<-Сторінка"),
                types.KeyboardButton(text=f"Сторінка->{next_number}"),
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="...",
    )

    return pagination_keyboard
