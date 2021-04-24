import telebot
from telebot import types
from config import *
import sqlite3


bot = telebot.TeleBot(token)

user_dict = {}

PRIVATE_CARD = '5168757413064025'

cigarettes = ['LM 55 ГРН', 'BOND 60 ГРН', 'MALBORO 50 ГРН']


class User:
    def __init__(self, room):
        self.room = room
        self.cigarete = None
        self.number = None
        self.comm = None


@bot.message_handler(commands=['start', 'help'])
def say_hello(message):
    bot.send_message(message.chat.id, "Приветствую👋.  Для того, чтобы"
                                      " купить сигареты, введите команду '/buy'. В течении 10 минут🕗, "
                                      "после оплаты, сигареты"
                                      " будут доставлены в вашу комнату.")


@bot.message_handler(commands=['buy'])
def send_buy(message):
    msg = bot.send_message(message.chat.id, 'Введи свою комнату')
    bot.register_next_step_handler(msg, process_room_step)


def process_room_step(message):
    if len(message.text) == 3:
        chat_id = message.chat.id
        room = message.text
        user = User(room)
        user_dict[chat_id] = user
        keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1, resize_keyboard=True)
        lm = types.KeyboardButton(text=cigarettes[0])
        bond = types.KeyboardButton(text=cigarettes[1])
        malboro = types.KeyboardButton(text=cigarettes[2])
        keyboard.add(lm, bond, malboro)
        msg = bot.send_message(message.chat.id, 'Выберите товар', reply_markup=keyboard)
        bot.register_next_step_handler(msg, process_ciga_step)
    else:
        exception(message)


def process_ciga_step(message):
    chat_id = message.chat.id
    cigarete = message.text
    if cigarete in cigarettes:
        user = user_dict[chat_id]
        user.cigarete = cigarete
        msg = bot.send_message(message.chat.id, 'Введи свой телефон')
        bot.register_next_step_handler(msg, number_step)
    else:
        exception(message)


def number_step(message):
    chat_id = message.chat.id
    number = message.text
    user = user_dict[chat_id]
    if len(number) == 13 or len(number) == 12 or len(number) == 10:
        user.number = number
        keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1, resize_keyboard=True)
        call = types.KeyboardButton(text='Позвонить')
        write = types.KeyboardButton(text='Написать в Телеграмм')
        back = types.KeyboardButton(text='Отменить заказ')
        keyboard.add(call, write, back)
        msg = bot.send_message(message.chat.id, 'Выберите удобный способ связи', reply_markup=keyboard)
        bot.register_next_step_handler(msg, call_or_write)
    else:
        exception(message)


def call_or_write(message):
    chat_id = message.chat.id
    comm = message.text
    user = user_dict[chat_id]
    if comm == 'Позвонить' or comm == 'Написать в Телеграмм':
        user.comm = comm
        cost = 0
        if user.cigarete == cigarettes[0]:
            cost = str(55)
        elif user.cigarete == cigarettes[1]:
            cost = str(60)
        elif user.cigarete == cigarettes[2]:
            cost = str(50)
        else:
            exception(message)
        bot.send_message(message.chat.id, 'Заказ принят. В течении 5 минут вам позвонит или напишет'
                                          ' оператор для подтверждения заказа.'
                                          f' После звонка оплатите {cost} ГРН')
        bot.send_message(message.chat.id, f'PRIVATE: {PRIVATE_CARD}\nMONOBANK: {PRIVATE_CARD}')
        database(message.chat.id, user.room, user.cigarete, user.number, user.comm)
    elif comm == 'Отменить заказ':
        bot.send_message(message.chat.id, 'Заказ отменен.')
    else:
        exception(message)


bot.enable_save_next_step_handlers(delay=3)

bot.load_next_step_handlers()


@bot.message_handler(content_types='text')
def all_text(message):
    bot.send_message(message.chat.id, "Не понимаю. Введите команду /buy и попытайтесь снова")


def database(userid, room, cigaretes, number, comm):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS orders
                      (id TEXT, room TEXT, cigaretes TEXT, number TEXT, communication TEXT)
                   """)
    conn.commit()
    cursor.execute(f"INSERT INTO orders VALUES (?, ?, ?, ?, ?)", (userid, room, cigaretes, number, comm))
    conn.commit()
    bot.send_message(614377323, f'Новый заказ!\nАйди: {userid}\nКомната: {room}\nСигареты: {cigaretes}\nНомер: {number}\n'
                                f'Способ контакта: {comm}')


def exception(message):
    bot.send_message(message.chat.id, 'Указанные данные неверны. Введите команду /buy и попытайтесь снова')


if __name__ == '__main__':
    bot.polling()