import time
import cherrypy
import os

import telebot

import conf

from dbhelper import get_user_sign
from prediction import read_prediction
from sign_define import parse_date, check_date, sign_define


token = os.environ.get('BOT_TOKEN')

WEBHOOK_PORT = int(os.environ.get('PORT', '5000'))
WEBHOOK_LISTEN = conf.webhook_listen

WEBHOOK_URL_BASE = conf.post_url
WEBHOOK_URL_PATH = "/{}/".format(token)

bot = telebot.TeleBot(token)


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    reply = conf.welcome
    bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=['horoscope'])
def send_horoscope(message):
    sign = get_user_sign(message.from_user.id)
    if sign:
        prediction = read_prediction(sign)
        reply = sign + conf.prediction.format(prediction[0], prediction[1])
    else:
        reply = conf.ask_date
    bot.send_message(message.chat.id, reply)


@bot.message_handler(regexp='ороскоп | oroscope')
def send_horoscope(message):
    sign = get_user_sign(message.from_user.id)
    if sign:
        prediction = read_prediction(sign)
        reply = sign[0] + conf.prediction.format(prediction[0], prediction[1])
    else:
        reply = conf.ask_date
    bot.send_message(message.chat.id, reply)


@bot.message_handler(regexp='[0-9][0-9]/[0-9][0-9]')
def send_day(message):
    day, month = parse_date(message.text)
    if check_date(day, month):
        sign = sign_define(message.from_user.id, day, month)
        try:
            prediction = read_prediction(sign)
            reply = sign + conf.prediction.format(prediction[0], prediction[1])
        except TypeError:
            reply = conf.confused
    else:
        reply = conf.wrong_date
    bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=['change'])
def change_sign(message):
    reply = conf.ask_date
    bot.send_message(message.chat.id, reply)


@bot.message_handler(func=lambda m: True)
def echo_all(message):
    reply = conf.confused
    bot.send_message(message.chat.id, reply)


class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)


if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(5)
    bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)

    cherrypy.config.update({
        'engine.autoreload.on': False,
        'server.socket_host': WEBHOOK_LISTEN,
        'server.socket_port': WEBHOOK_PORT,
    })

    # RUN SERVER, RUN!
    cherrypy.tree.mount(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})

    cherrypy.engine.start()
    cherrypy.engine.block()
    # bot.polling()
