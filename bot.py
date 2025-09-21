import socket
import requests
import random
import os

from dotenv import load_dotenv
from keep_alive import keep_alive

keep_alive()

load_dotenv()

token = os.getenv("TWITCH_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

server = 'irc.chat.twitch.tv'
port = 6667
nickname = '6otihok_kyky'
channel = '#skevich_'
# channel = '#hapurab_i_iiochigab'

CRYPTO_IDS = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "doge": "dogecoin",
    "ltc": "litecoin"
}

sock = socket.socket()
sock.connect((server, port))

sock.send(f"PASS {token}\r\n".encode('utf-8'))
sock.send(f"NICK {nickname}\r\n".encode('utf-8'))
sock.send(f"JOIN {channel}\r\n".encode('utf-8'))


print("Бот запущений, чекаємо повідомлень...")

def send_message(nick, msg):
    msg = f'@{nick} {msg}'
    sock.send(f"PRIVMSG {channel} :{msg}\r\n".encode('utf-8'))

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=uk"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("cod") != 200:
            return f"Не вдалося знайти місто {city}"
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        return f"У {city.title()} зараз {temp}°C, {desc}"
    except Exception as e:
        print(f"Помилка при отриманні погоди: {e}")
        return None
    
def get_crypto_rate(symbol):
    symbol = symbol.lower()
    crypto_id = CRYPTO_IDS.get(symbol)
    if not crypto_id:
        return f"Не знайдено криптовалюту {symbol.upper()}"
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        price = data[crypto_id]['usd']
        return f"Курс {symbol.upper()} зараз {price} $"
    except Exception as e:
        print(f"Помилка при отриманні курсу: {e}")
        return None

def get_currency_rate(currency):
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        currency = currency.upper()
        for item in data:
            if item["cc"] == currency:
                return f"Сьогодні курс {currency} = {item['rate']} грн"
        print(f"Не знайдено валюту {currency}")
        return None
    except Exception as e:
        print(f"Помилка при отриманні курсу: {e}")
        return None
    
def define_nick_rule(nick):
    nicks_dict = {
        'skevich_': 'Short',
        'fazzlk': 'Banana'
    }
    return nicks_dict.get(nick)

def skelya_description(skelya_size):
    if skelya_size < 4:
        return "плакали усім чатом BibleThump"
    elif skelya_size < 10:
        return "щось на середньостатистичному (у холодній воді) zaga"
    elif skelya_size < 15:
        return "фазлік починає заздрити WHAT"
    else:
        return "напиши мені в інстраграмі, аккаунт skevichh NOTED"
    
def get_skelya_size(nick):
    rule = define_nick_rule(nick)
    text = 'розмір твоєї скелі '
    skelya_size = 0
    if not rule:
        skelya_size = random.randint(1, 20)
        text += f'{skelya_size}'
        text += ' см, '
        text += skelya_description(skelya_size)
    else:
        if rule == 'Short':
            skelya_size = random.randint(1, 4)
            text += f'{skelya_size}'
            text += ' см, '
            text += skelya_description(skelya_size)
        elif rule == 'Banana':
            text = 'уууу ааа ауаууа у 2-3  🍌  🍌  🍌 '
    return text

while True:
    resp = sock.recv(4096).decode('utf-8', errors='ignore')

    for line in resp.split('\r\n'):
        if not line:
            continue

        # відповідаємо на PING
        if line.startswith('PING'):
            sock.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
            continue

        if "PRIVMSG" in line:
            try:
                # текст повідомлення
                nick = line.split("!")[0][1:]
                text = line.split(":", 2)[2].strip()
            except IndexError:
                continue

            # команди
            if text.strip() == "!білд":
                reply = "БІЛД НА ЕЛДЕН РІНГ - максимо віру 1 до 2, тобто, я можу мати 30 віри, тільки після цього можу качнути будь який інший стат до 15. ЗБРОЯ БУДЬ ЯКА ЩО МАЄ В СОБІ СКЕЙЛ ВІРИ. АРМОР БУДЬ ЯКИЙ"
                send_message(nick, reply)

            elif text.strip() == "!скеля":
                reply = get_skelya_size(nick)
                send_message(nick, reply)
                
            elif text.strip() == "!дедлок":
                reply = "дедлок? ахах, я думав ця гра вже давно здохла LOLOL"
                send_message(nick, reply)

            elif text.startswith("!погода"):
                parts = text.split(maxsplit=1)
                if len(parts) == 2:
                    city = parts[1]
                    reply = get_weather(city)
                    if reply:
                        send_message(nick, reply)


            elif text.startswith("!курс_крипти"):
                parts = text.split(maxsplit=1)
                if len(parts) == 2:
                    crypto = parts[1]
                    reply = get_crypto_rate(crypto)
                    if reply:
                        send_message(nick, reply)

            elif text.startswith("!курс"):
                parts = text.split(maxsplit=1)
                if len(parts) == 2:
                    currency = parts[1]
                    reply = get_currency_rate(currency)
                    if reply:
                        send_message(nick, reply)                      
                