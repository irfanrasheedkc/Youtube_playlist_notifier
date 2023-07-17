from keep_alive import keep_alive
keep_alive()

import os
import telebot
import requests

from datetime import datetime, timezone, timedelta
import time

from pymongo import MongoClient

import threading

# Set up the MongoDB client and connect to the database
client = MongoClient("mongodb+srv://irfanrasheedkc:gTo5RnpsY7mpL2BZ@cluster0.mznznpy.mongodb.net/?retryWrites=true&w=majority")
db = client['Youtube_Bot']  # Replace 'my_youtube_db' with your preferred database name
collection = db['Playlist']

# Replace 'YOUR_API_KEY' with your actual bot token obtained from BotFather
API_KEY = '6302131174:AAG_j85v1Tf4GUNW1uIaR0_gHY1Oue1WmWQ'

bot = telebot.TeleBot(API_KEY)


# Welcome message and options for the user
start_message = "Hello! I am your YouTube playlist bot. How can I assist you?\n" \
                "1. /add_playlist - Add a new playlist.\n"\
                "2. /get_latest_video - Get the last video.\n"\
                "3. /get_playlist - Get all  playlists.\n"


def get_all_playlists():
    all_playlists = collection.find({}, {'_id': 0, 'title': 1, 'link': 1})
    return list(all_playlists)

def send_all_playlists(chat_id):
    playlists = get_all_playlists()
    if playlists:
        message = "List of all playlists:\n"
        for playlist in playlists:
            message += f"{playlist['title']}: {playlist['link']}\n"
        bot.send_message(chat_id, message)
    else:
        bot.send_message(chat_id, "No playlists found in the database.")

@bot.message_handler(commands=['get_playlist'])
def get_playlist_handler(message):
    chat_id = message.chat.id
    send_all_playlists(chat_id)

def get_last_video_info(playlist_id):
    base_url = 'https://www.googleapis.com/youtube/v3/playlistItems'
    playlist_id = playlist_id.split("list=")[-1]
    print(f"Playlist id:{playlist_id}")
    params = {
        'key': "AIzaSyB7q2z7ski2Vs2Hb4Aa1LPBzEE7hIMKKks",
        'part': 'snippet',
        'playlistId': playlist_id,
        'maxResults': 1,
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    print(data)
    if 'items' in data and len(data['items']) > 0:
        last_video_info = data['items'][0]['snippet']
        print(f"Last video Info {last_video_info}")
        video_title = last_video_info['title']
        video_link = f"https://www.youtube.com/watch?v={last_video_info['resourceId']['videoId']}"
        return video_title, video_link
    else:
        return None, None
        
def send_latest_video(chat_id, playlist_id):
    playlist_title, last_video_time = get_playlist_info(playlist_id)
    if playlist_title and last_video_time:
        latest_video_title, latest_video_link = get_last_video_info(playlist_id)
        if latest_video_title and latest_video_link:
            message = f"Latest video in playlist '{playlist_title}'\nTitle: {latest_video_title}\nLink: {latest_video_link}"
            bot.send_message(chat_id, message)
        else:
            bot.send_message(chat_id, "No videos found in the playlist.")
    else:
        bot.send_message(chat_id, "Invalid playlist ID. Please try again.")

@bot.message_handler(commands=['get_latest_video'])
def get_latest_video_handler(message):
    bot.reply_to(message, "Please enter the YouTube playlist link to get the latest video:")
    bot.register_next_step_handler(message, process_latest_video_request)

def process_latest_video_request(message):
    playlist_link = message.text.strip()
    chat_id = message.chat.id
    send_latest_video(chat_id, playlist_link)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, start_message)

@bot.message_handler(commands=['add_playlist'])
def add_playlist(message):
    bot.reply_to(message, "Please enter the YouTube playlist link as a reply to this message:")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Check if the user is responding to the /add_playlist command
    if message.reply_to_message and message.reply_to_message.text == "Please enter the YouTube playlist link as a reply to this message:":
        playlist_link = message.text.strip()
        print(playlist_link)
        user_chat_id = message.chat.id
        playlist_title = get_playlist_title(playlist_link,user_chat_id)
        if playlist_title:
            bot.reply_to(message, f"Playlist title: {playlist_title}")
        else:
            bot.reply_to(message, "Invalid playlist link. Please try again.")

    else:
        # If the user sends any other message, respond with the start message and options
        bot.reply_to(message, start_message)

def convert_to_indian_time(utc_time_str):
    utc_time = datetime.strptime(utc_time_str, '%Y-%m-%dT%H:%M:%SZ')
    ist_time = utc_time.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30)))
    return ist_time.strftime('%Y-%m-%d %H:%M:%S')

def get_playlist_title(playlist_link,user_chat_id):
    try:
        playlist_id = playlist_link.split("list=")[-1]
        base_url = 'https://www.googleapis.com/youtube/v3/playlists'
        params = {
            'key': 'AIzaSyB7q2z7ski2Vs2Hb4Aa1LPBzEE7hIMKKks',
            'part': 'snippet',
            'id': playlist_id,
        }
        response = requests.get(base_url, params=params)
        data = response.json()

        if 'items' in data and len(data['items']) > 0:

            playlist_title, last_video_time = get_playlist_info(playlist_link)
            last_video_time = convert_to_indian_time(last_video_time)
            if playlist_title:
                # Insert the playlist link and last video time into the database
                playlist_data = {
                    'link': playlist_link,
                    'title': playlist_title,
                    'last_video_time': last_video_time,
                    'user_chat_id': user_chat_id
                }
                collection.insert_one(playlist_data)

            return playlist_title
    
        else:
            return None

    except Exception as e:
        print("Error:", e)
        return None

def get_last_video_time(playlist_id):
    base_url = 'https://www.googleapis.com/youtube/v3/playlistItems'
    params = {
        'key': 'AIzaSyB7q2z7ski2Vs2Hb4Aa1LPBzEE7hIMKKks',
        'part': 'snippet',
        'playlistId': playlist_id,
        'maxResults': 1,
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    if 'items' in data and len(data['items']) > 0:
        last_video_time = data['items'][0]['snippet']['publishedAt']
        return last_video_time
    else:
        return None

def get_playlist_info(playlist_link):
    try:
        playlist_id = playlist_link.split("list=")[-1]
        base_url = 'https://www.googleapis.com/youtube/v3/playlists'
        params = {
            'key': 'AIzaSyB7q2z7ski2Vs2Hb4Aa1LPBzEE7hIMKKks',
            'part': 'snippet',
            'id': playlist_id,
        }
        response = requests.get(base_url, params=params)
        data = response.json()

        if 'items' in data and len(data['items']) > 0:
            playlist_title = data['items'][0]['snippet']['title']
            last_video_time = get_last_video_time(playlist_id)
            return playlist_title, last_video_time
        else:
            return None, None

    except Exception as e:
        print("Error:", e)
        return None, None

def send_notification(user_chat_id, playlist_title, playlist_link , latest_video_title , latest_video_link , last_video_time):
    message = f"New video added to playlist '{playlist_title}'\n"
    message += f"Title: {latest_video_title}\n"
    message += f"Link: {latest_video_link}\n"
    message += f"Published Time (IST): {convert_to_indian_time(last_video_time)}"

    try:
        bot.send_message(user_chat_id, message)
        # Update the last_video_time in the database only after the notification is successfully sent
        collection.update_one({'link': playlist_link}, {'$set': {'last_video_time': last_video_time}})
    except Exception as e:
        print(f"Error sending notification to user {user_chat_id}: {e}")

def check_playlists():
    playlists = collection.find()
    for playlist_info in playlists:
        playlist_title = playlist_info['title']
        playlist_link = playlist_info['link']
        last_db_video_time = playlist_info.get('last_video_time')

        last_api_video_time = get_last_video_time(playlist_link)
        if not last_api_video_time:
            continue

        # Convert UTC time to Indian Standard Time (IST)
        last_api_video_time_ist = convert_to_indian_time(last_api_video_time)

        if last_db_video_time and last_api_video_time != last_db_video_time:
            # New video found, notify the user
            user_chat_id = playlist_info['user_chat_id']
            playlist_id = playlist_link.split("list=")[-1]
            latest_video_title, latest_video_link = get_last_video_info(playlist_id)
            message = f"New video added to playlist '{playlist_title}'\nLast Video Time (IST): {last_api_video_time_ist}"
            send_notification(user_chat_id, playlist_title, playlist_link , latest_video_title , latest_video_link , last_api_video_time)

            # Update the last_video_time in the database
            collection.update_one({'_id': playlist_info['_id']}, {'$set': {'last_video_time': last_api_video_time}})
        elif not last_db_video_time:
            # This is the first time checking, so just update the last_video_time in the database
            collection.update_one({'_id': playlist_info['_id']}, {'$set': {'last_video_time': last_api_video_time}})

def start_routine_checking(interval_minutes):
    while True:
        check_playlists()
        print("Routine checking complete. Waiting for the next check...")
        time.sleep(interval_minutes * 60)  # Convert minutes to seconds

# Function to run the bot
def run_bot():
    # Start the bot
    bot.polling()

# Function to stop the MongoDB client after the bot stops polling
def stop_mongodb_client():
    client.close()

# Run the bot and the routine checking
if __name__ == '__main__':
    try:
        # Start the routine checking in a separate thread
        interval_minutes = 0.1
        checking_thread = threading.Thread(target=start_routine_checking, args=(interval_minutes,))
        checking_thread.start()

        # Run the bot
        run_bot()

    finally:
        # Call the function to stop the MongoDB client
        stop_mongodb_client()