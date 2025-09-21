import socket
import requests
import random
import os
import time

from dotenv import load_dotenv

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

# ------------------- Методи -------------------

def connect_to_twitch():
    while True:
        try:
            sock = socket.socket()
            sock.connect((server, port))
            sock.send(f"PASS {token}\r\n".encode('utf-8'))
            sock.send(f"NICK {nickname}\r\n".encode('utf-8'))
            sock.send(f"JOIN {channel}\r\n".encode('utf-8'))
            print("Успішно підключено до Twitch IRC")
            return sock
        except Exception as e:
            print(f"[!] Помилка підключення: {e}. Повтор через 10 секунд")
            time.sleep(10)

def send_message(sock, nick, msg):
    try:
        msg_full = f"@{nick} {msg}"
        sock.send(f"PRIVMSG {channel} :{msg_full}\r\n".encode('utf-8'))
        print(f"[=>] Відправлено повідомлення: {msg_full}")
    except Exception as e:
        print(f"[!] Помилка відправки повідомлення: {e}")

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
        print(f"[!] Помилка при отриманні погоди: {e}")
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
        print(f"[!] Помилка при отриманні курсу крипти: {e}")
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
        return f"Не знайдено валюту {currency}"
    except Exception as e:
        print(f"[!] Помилка при отриманні курсу валют: {e}")
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
    if not rule:
        skelya_size = random.randint(1, 20)
        return f"розмір твоєї скелі {skelya_size} см, {skelya_description(skelya_size)}"
    elif rule == 'Short':
        skelya_size = random.randint(1, 4)
        return f"розмір твоєї скелі {skelya_size} см, {skelya_description(skelya_size)}"
    elif rule == 'Banana':
        return 'уууу ааа ауаууа у 2-3  🍌  🍌  🍌 '

# ------------------- Основний цикл -------------------

sock = connect_to_twitch()
print("Бот запущений, чекаємо повідомлень...")

while True:
    try:
        resp = sock.recv(4096).decode('utf-8', errors='ignore')
        if not resp:
            raise Exception("Отримано пустий пакет, перепідключення...")
    except Exception as e:
        print(f"[!] Помилка recv(): {e}")
        sock.close()
        sock = connect_to_twitch()
        continue

    for line in resp.split('\r\n'):
        if not line:
            continue

        # PING/PONG
        if line.startswith('PING'):
            try:
                sock.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
                print("[<=>] Відправлено PONG")
            except Exception as e:
                print(f"[!] Помилка PONG: {e}")
            continue

        # Приватні повідомлення
        if "PRIVMSG" in line:
            try:
                nick = line.split("!")[0][1:]
                text = line.split(":", 2)[2].strip()
                print(f"[<=] Отримано повідомлення від {nick}: {text}")
            except Exception as e:
                print(f"[!] Помилка обробки повідомлення: {e}")
                continue

            # Команди
            if text.strip() == "!білд":
                reply = "БІЛД НА ЕЛДЕН РІНГ - максимо віру 1 до 2..."
                send_message(sock, nick, reply)
            elif text.strip() == "!скеля":
                send_message(sock, nick, get_skelya_size(nick))
            elif text.strip() == "!дедлок":
                send_message(sock, nick, "дедлок? ахах, я думав ця гра вже давно здохла LOLOL")
            elif text.startswith("!погода"):
                parts = text.split(maxsplit=1)
                if len(parts) == 2:
                    reply = get_weather(parts[1])
                    if reply:
                        send_message(sock, nick, reply)
            elif text.startswith("!курс_крипти"):
                parts = text.split(maxsplit=1)
                if len(parts) == 2:
                    reply = get_crypto_rate(parts[1])
                    if reply:
                        send_message(sock, nick, reply)
            elif text.startswith("!курс"):
                parts = text.split(maxsplit=1)
                if len(parts) == 2:
                    reply = get_currency_rate(parts[1])
                    if reply:
                        send_message(sock, nick, reply)
