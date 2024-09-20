import json
import os
from dotenv import load_dotenv
import base64
from requests import post, get
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()


def get_token(client_id, client_secret):
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials"
    }
    result = post(url, headers=headers, data=data)
    return json.loads(result.content).get("access_token")


def get_playlist_tracks(token, playlist_id, market="TR"):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "market": market
    }
    result = get(url, headers=headers, params=params)
    return json.loads(result.content)


def count_songs_by_user(playlist_tracks):
    user_song_count = dict()
    user_songs = dict()

    for item in playlist_tracks['items']:
        user_id = item['added_by']['id']
        if user_id in user_song_count:
            user_song_count[user_id] += 1
        else:
            user_song_count[user_id] = 1

        if user_id in user_songs:
            user_songs[user_id].append(item['track']['name'])
        else:
            user_songs[user_id] = [item['track']['name']]

    return user_song_count, user_songs


import requests


def get_user_info(token, user_id):
    url = f"https://api.spotify.com/v1/users/{user_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None


def format_user_songs(token, user_song_count, user_songs):
    result = ""
    for user_id, count in user_song_count.items():
        user_info = get_user_info(token, user_id)
        if user_info:
            name = user_info['display_name']
            spotify_url = user_info['external_urls']['spotify']

            result += f"**Name**: {name}\n"
            result += f"**Spotify Account Link**: {spotify_url}\n"
        else:
            result += f"**Id**: {user_id}\n"

        result += f"**Song Count**: {count}\n"
        result += "Songs:\n"

        for song in user_songs[user_id]:
            result += f"- [{song}]\n"
        result += "\n"
    return result


def send_email(subject, body, recipient_email):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    server.login(sender_email, sender_password)

    server.sendmail(sender_email, recipient_email, message.as_string())

    server.quit()


def main():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    playlist_id = "5lREYWqVljsh96Dj7TkkMH"
    recipient_email = os.getenv("RECIPIENT_EMAIL")

    token = get_token(client_id, client_secret)

    playlist_tracks = get_playlist_tracks(token, playlist_id)

    user_song_count, user_songs = count_songs_by_user(playlist_tracks)

    formatted_output = format_user_songs(token, user_song_count, user_songs)

    send_email("Spotify kiki Playlist Report", formatted_output, recipient_email)
    print(formatted_output)


if __name__ == '__main__':
    main()

