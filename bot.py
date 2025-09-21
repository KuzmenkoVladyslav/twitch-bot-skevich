import socket
import requests
import random
import os
import time

from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TWITCH_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

server = 'irc.chat.twitch.tv'
port = 6667
nickname = '6otihok_kyky'
channel = '#skevich_'

CRYPTO_IDS = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "doge": "dogecoin",
    "ltc": "litecoin"
}

def connect_to_twitch():
    while True:
        try:
            sock = socket.socket()
            sock.connect((server, port))
            sock.send(f"PASS {token}\r\n".encode('utf-8'))
            sock.send(f"NICK {nickname}\r\n".encode('utf-8'))
            sock.send(f"JOIN {channel}\r\n".encode('utf-8'))

            sock.settimeout(10)
            try:
                resp = sock.recv(4096).decode('utf-8', errors='ignore')
                print(f"Initial response from Twitch: {resp}")  # Add this for debugging
                if resp:
                    if "Login authentication failed" in resp or "Error logging in" in resp:
                        print("Authentication failed! Check your token.")
                        sock.close()
                        time.sleep(10)
                        continue
                    print("Успішно підключено до Twitch IRC")
                    sock.settimeout(None)
                    return sock
            except socket.timeout:
                print("Не отримано відповідь від IRC, повторне підключення через 10 секунд")
                sock.close()
                time.sleep(10)

        except Exception as e:
            print(f"Помилка підключення: {e}, повтор через 10 секунд")
            time.sleep(10)

def send_message(sock, nick, msg):
    try:
        msg_full = f"@{nick} {msg}"
        sock.send(f"PRIVMSG {channel} :{msg_full}\r\n".encode('utf-8'))
        print(f"[=>] Відправлено повідомлення: {msg_full}")
    except Exception as e:
        print(f"[!] Помилка відправки повідомлення: {e}")

def ask_groq(question):
    if not GROQ_API_KEY:
        print("API-ключ не налаштовано. Звернись до адміністратора.")
        return None
    
    system_prompt = """
    Ти веселий мемний бот для українського Twitch-чату.
    - Відповідай ТІЛЬКИ на українській мові, коротко (1-3 речення, max 80 слів).
    - Використовуй правильну українську граматику, природний розмовний стиль (без помилок у відмінках, роді чи часах).
    - Якщо питання жартівливе — відповідай з гумором, емодзі та Twitch-емотами (Kappa, BibleThump, PogChamp).
    - Будь чесним: базуйся на загальновідомих фактах, не вигадуй. Якщо не знаєш — скажи "Не впевнений, але..." і порадь шукати.
    - Для стримерів/геймерів: додай Twitch-деталі (посилання, ігри).".
    """
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {
                "role": "system", 
                "content": system_prompt
            },
            {
                "role": "user", 
                "content": question
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7,
        "top_p": 0.9
    }
    
    try:
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"[!] Groq помилка: {r.status_code} - {r.text}")
            return "Щось пішло не так з AI. Спробуй пізніше!"
        
        data = r.json()
        answer = data['choices'][0]['message']['content'].strip()
        return answer
    except Exception as e:
        print(f"[!] Помилка Groq: {e}")
        return "Помилка з'єднання з AI."

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=uk"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("cod") != 200:
            print(f"Не вдалося знайти місто {city}")
            return None
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
        print(f"Не знайдено криптовалюту {symbol.upper()}")
        return None
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
        print(f"Не знайдено валюту {currency}")
        return None
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

sock = connect_to_twitch()
print("Бот запущений, чекаємо повідомлень...")

while True:
    try:
        resp = sock.recv(4096).decode('utf-8', errors='ignore')
        if resp:
            print(f"Received data: {resp}")
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

        if line.startswith('PING'):
            try:
                sock.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
                print("[<=>] Відправлено PONG")
            except Exception as e:
                print(f"[!] Помилка PONG: {e}")
            continue

        if "PRIVMSG" in line:
            try:
                nick = line.split("!")[0][1:]
                text = line.split(":", 2)[2].strip()
                print(f"[<=] Отримано повідомлення від {nick}: {text}")
            except Exception as e:
                print(f"[!] Помилка обробки повідомлення: {e}")
                continue

            if text.strip() == "!білд":
                reply = "БІЛД НА ЕЛДЕН РІНГ - максимо віру 1 до 2, тобто, я можу мати 30 віри, тільки після цього можу качнути будь який інший стат до 15. ЗБРОЯ БУДЬ ЯКА ЩО МАЄ В СОБІ СКЕЙЛ ВІРИ. АРМОР БУДЬ ЯКИЙ"
                send_message(sock, nick, reply)
            elif text.strip() == "!сбу" or text.strip() == "!СБУ":
                reply = "Шановний Малюк Василь Васильович! Хочу повідомити, що я не маю жодного відношення до цього каналу. Я випадково потрапив сюди, нічого не поширював, нічого не завантажував, не лайкав і не репостив. Мене підставили. Прошу врахувати це під час досудового слідства. Слава Україні!"
                send_message(sock, nick, reply)
            elif text.strip() == "!обс":
                reply = "Підкажи як правильно працювати з ОБС, чи можеш продемонструвати функцію закінчити трансляцію?"
                send_message(sock, nick, reply)
            elif text.strip() == "!хуйня":
                reply = "почитав чат, дякую, зайду пізніше, місяці через 2"
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
            elif text.startswith("!питання"):
                parts = text.split(maxsplit=1)
                if len(parts) == 2:
                    reply = ask_groq(parts[1])
                    send_message(sock, nick, reply)
            elif "ы" in text or "э" in text:
                reply = 'Свий сука ReallyMad'
                send_message(sock, nick, reply)
            elif text.strip() == "!help":
                reply = "Доступні команди: !білд, !скеля, !дедлок, !погода [місто], !курс_крипти [назва крипти], !курс [назва валюти з НБУ], !сбу, !обс, !хуйня, !питання [твоє питання]"
                send_message(sock, nick, reply)

