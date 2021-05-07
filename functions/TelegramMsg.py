import telegram


def SendMsg(msg):
    chat_token = "1474721655:AAH7cSJoNQdesO_lXRRGUf__mGIInPpicdU"
    bot = telegram.Bot(token = chat_token)
    bot.send_message(chat_id = "1542664370", text = msg)
