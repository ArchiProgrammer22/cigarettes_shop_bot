import telebot
from telebot import types

import config
import message_patterns
from user import User

call_or_message_actions = ('Позвонить', 'Написать в Телеграмм', 'Отменить заказ')

bot = telebot.TeleBot(config.BOT_TOKEN)

user_dict: dict[int, User] = {}


@bot.message_handler(commands=['start', 'help'])
def handle_command_start(message: types.Message):
    bot.send_message(message.chat.id, message_patterns.welcome)


@bot.message_handler(commands=['buy'])
def handle_command_buy(message: types.Message):
    msg = bot.send_message(message.chat.id, message_patterns.enter_room)
    bot.register_next_step_handler(msg, handle_room_step)


def handle_room_step(message: types.Message):
    if not message.text.isdigit() or len(message.text) != 3:
        bot.send_message(message.chat.id, message_patterns.enter_exception)
        handle_command_buy(message)
        return

    user_dict[message.chat.id] = User(room=message.text)

    reply_markup = types.InlineKeyboardMarkup(
        keyboard=[
            [types.InlineKeyboardButton(text=f'{product} {price} грн.', callback_data=product)]
            for product, price in config.PRODUCTS.items()
        ],
        row_width=1
    )

    bot.send_message(message.chat.id, message_patterns.choose_product, reply_markup=reply_markup)


@bot.callback_query_handler(func=lambda callback: callback.data in config.PRODUCTS.keys())
def handle_product_query(callback: types.CallbackQuery):
    user_dict[callback.message.chat.id].product = callback.data
    bot.answer_callback_query(callback.id, message_patterns.selected_product.format(callback.data))
    bot.delete_message(callback.message.chat.id, callback.message.id)

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    reply_markup.add(types.KeyboardButton('Отправить номер телефона', True))

    msg = bot.send_message(callback.message.chat.id, message_patterns.send_phone, reply_markup=reply_markup)
    bot.register_next_step_handler(msg, handle_phone)


def handle_phone(message: types.Message):
    user_dict[message.chat.id].phone = '+' + message.contact.phone_number

    reply_markup = types.InlineKeyboardMarkup(
        keyboard=[
            [types.InlineKeyboardButton(item, callback_data=item)]
            for item in call_or_message_actions
        ],
        row_width=1
    )

    bot.send_message(message.chat.id, message_patterns.call_or_message, reply_markup=reply_markup)


@bot.callback_query_handler(func=lambda callback: callback.data in call_or_message_actions)
def handle_call_or_message(callback: types.CallbackQuery):
    bot.delete_message(callback.message.chat.id, callback.message.id)
    if callback.data == call_or_message_actions[-1]:
        bot.send_message(callback.message.chat.id, message_patterns.cancel_order, reply_markup=types.ReplyKeyboardRemove())
        return

    user_dict[callback.message.chat.id].call_or_message = callback.data
    bot.answer_callback_query(callback.id, message_patterns.selected_product.format(callback.data))
    bot.send_message(
        chat_id=callback.message.chat.id,
        text=message_patterns.successful_order.format(config.PRODUCTS[user_dict[callback.message.chat.id].product]),
        reply_markup=types.ReplyKeyboardMarkup(True, True).add(types.KeyboardButton('/buy'))
    )

    bot.send_message(callback.message.chat.id, f'PRIVATE: {config.PRIVATE_CARD}')

    bot.send_message(
        chat_id=config.ADMIN_ID,
        text=f'Новый заказ!\n'
             f'ID: {callback.message.chat.id}\n'
             f'{"Username: @{}".format(callback.from_user.username) if callback.from_user.username else ""}\n'
             f'Комната: {user_dict[callback.message.chat.id].room}\n'
             f'Товар: {user_dict[callback.message.chat.id].product}\n'
             f'Цена: {config.PRODUCTS[user_dict[callback.message.chat.id].product]} грн.\n'
             f'Номер: {user_dict[callback.message.chat.id].phone}\n'
             f'Способ контакта: {user_dict[callback.message.chat.id].call_or_message}'
    )


@bot.message_handler(content_types='text')
def handle_other_text(message):
    bot.send_message(message.chat.id, "Не понимаю. Введите команду /buy и попытайтесь снова")


if __name__ == '__main__':
    bot.polling()
