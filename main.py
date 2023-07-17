from keep_alive import keep_alive
keep_alive()

import os
import telebot
import requests

from pymongo import MongoClient

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
                "3. /get_all_playlist - Get all subscribed playlists.\n"


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
        playlist_title = get_playlist_title(playlist_link)
        if playlist_title:
            bot.reply_to(message, f"Playlist title: {playlist_title}")
        else:
            bot.reply_to(message, "Invalid playlist link. Please try again.")

    else:
        # If the user sends any other message, respond with the start message and options
        bot.reply_to(message, start_message)

def get_playlist_title(playlist_link):
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
            if playlist_title:
                # Insert the playlist link and last video time into the database
                playlist_data = {
                    'link': playlist_link,
                    'title': playlist_title,
                    'last_video_time': last_video_time,
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

# Start the bot
bot.polling()