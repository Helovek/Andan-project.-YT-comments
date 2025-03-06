from fileinput import lineno
from http.client import responses
from idlelib.replace import replace

import pandas as pd
import numpy as np
import scipy.stats as sts
import json
import os
import re
import time
import datetime
import sqlite3
import googleapiclient
from numpy.random.mtrand import standard_t
from tqdm.notebook import tqdm
from googleapiclient.discovery import build


api_key = "AIzaSyBcH24rIhGpB1Z4zhVi2Cx-mTdK0K7WvIg"

def errors(text):
    with open ('errors.txt', 'a', encoding='utf-8') as file:
        file.write(text)

def channels_id(paths_to_list):
    """
    :param paths_to_list: link to channels list
    :return: id of channels

    Функция преобразовывает ссылки на каналы в список id.
    Так и не понял, полностью ли ютуб перешел на кастомные url каналов,
    поэтому оставил возможность если что добавить другую маску
    для регулярных выражений
    """

    youtube = build("youtube", "v3", developerKey=api_key)
    custom_url = r'https?://(?:www\.)?youtube\.com/@([A-Za-z0-9_-]+)'




    channels_list = pd.read_csv(paths_to_list, sep=';')
    nik_list = []

    for i in channels_list.index:
        match_custom_url = re.match(custom_url, channels_list.loc[i][0])
        ### здесь был мэтч для стандартного url

        custom = None # используем None для проверки, все ли идет по плану

        if match_custom_url:
            custom = True

        if custom:
            nik_list.append(match_custom_url.group(1))
        else:
            nik_list.append(f'Error. Nonstandard url: {channels_list.loc[i][0]}')

    err = 'Error'
    id_list = []

    for i in nik_list:
        if i[:5] != err:
            request = youtube.search().list(
                part='snippet',
                q=i,
                type="channel",
                maxResults=1
            )
            response = request.execute()
            id_list.append(response['items'][0]['id']['channelId'])
        else:
            id_list.append(i)

    ### соединяем ссылки и id в одну таблицу и выводим
    channels_list['id']=id_list

    return channels_list

def videos(channel):
    youtube = build("youtube", "v3", developerKey=api_key)
    videos_dict = {'channel': [],
                   'video': [],
                   'publish_date': []}
    next_page_token = None
    one_month = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)

    request = youtube.channels().list(
        id=channel,
        part='contentDetails'
    )
    response = request.execute()
    uploads_list = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']


    while True:
        try:
            request = youtube.playlistItems().list(
                playlistId=uploads_list,
                part='contentDetails',
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get('items', []):
                video = item['contentDetails']['videoId']
                publish_date = datetime.datetime.fromisoformat(item['contentDetails']['videoPublishedAt'].replace('Z', '+00:00'))

                if publish_date >= one_month:
                    videos_dict['channel'].append(channel)
                    videos_dict['video'].append(video)
                    videos_dict['publish_date'].append(publish_date)

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        except googleapiclient.errors.HttpError as err:
            errors(f"Ошибка в videos(): {err}, {next_page_token}")

    return videos_dict

def get(video_id):
    youtube = build("youtube", "v3", developerKey=api_key)

    comments = []
    next_page_token = None

    while True:
        try:
            request = youtube.commentThreads().list(
                part='snippet,replies',
                videoId=video_id,
                maxResults=100,
                textFormat='plainText',
                pageToken=next_page_token
            )
            response = request.execute()  # make request to google

            for i in response.get("items", []):
                hed_tread = i['snippet']['topLevelComment'] # извлекаем комментарий из ветки
                comment_data = {
                    'userId': hed_tread['snippet']['authorChannelId']['value'],
                    'commentDate': hed_tread['snippet']['publishedAt'],
                    'likeCount': hed_tread['snippet']['likeCount'],
                    'totalReplyCount': i['snippet']['totalReplyCount'],
                    'videoId': video_id,
                    'commentText': hed_tread['snippet']['textDisplay']
                }
                comments.append(comment_data)
            next_page_token = response.get("nextPageToken")

            # выходим из while, если комментарии закончились
            if not next_page_token: break
            time.sleep(0.5)
        except googleapiclient.errors.HttpError as err:
            errors(f"Ошибка: {err}, {video_id}, {next_page_token}")

    comments = pd.DataFrame(comments)
    return comments

def second_mode(channels):
    videos_dict = {'channel': [],
                   'video': [],
                   'publish_date': []}

    df = pd.read_json(channels)

    for i in df['id']:
        response = videos(i)
        videos_dict['channel'].append(response['channel'])
        videos_dict['video'].append(response['video'])
        videos_dict['publish_date'].append(response['publish_date'])

    return videos_dict


def third_mode(videos_list):
    connection = sqlite3.connect('my_database.db')
    cursor = connection.cursor()

    cursor.execute('''
    CREATE TABEL IF NOT EXIST comments(
    channelId TEXT NOT NULL
    videoId TEXT NOT NULL
    userId TEXT NOT NULL
    videoDate DATETIME 
    commentDate DATETIME 
    commentText TEXT NOT NULL
    likeCount INTEGER
    totalReplyCount INTEGER
    )
    ''')
    for (channelId, videoId, videoDate) in videos_list:
        comments = get(videoId)
        comments['videoDate'] = videoDate
        comments['channelId'] = channelId

        comments = comments['channelId', 'videoId', 'userId', \
            'videoDate', 'commentDate', 'commentText', 'likeCount', \
            'totalReplyCount']

        # добавляем данные из таблицы в базу
        for row in comments.itertuples():
            cursor.execute('INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?, ?, ?)', row)
    #закрываем базу данных
    connection.commit()





print("""
Выберете режим работы:
1 -- Обработка списка каналов и преобразование из в список
2 -- Создание списков id видео за последний месяц для списка каналов
3 -- создание базы данных комментариев под видео
""")
operating_mode = int(input('Введите номер режима работы: '))

if operating_mode == 1:
    link = input('Выбран режим обработки списков каналов. Введите ссылку на список: ')
    tabel = channels_id(link)
    tabel.to_json('channels_df.json')
    print(f'Файл сохранен под именем channels_df.json в директории: {os.getcwd()}')
elif operating_mode == 2:
    print('Выбран режим создания списков id видео за последний месяц.')
    link = input('Введите ссылку на список каналов (если хотите использовать\
    из режима 1 -- введите d): ')
    if link == 'd':
        videos_df = pd.DataFrame(second_mode('channels_df.json'))
        videos_df.to_json('videos.json')
    else:
        videos_df = pd.DataFrame(second_mode('link'))
        videos_df.to_json('videos.json')
elif operating_mode == 3:
    print("""
    Выбран режим создания базы данных. Если хотите использовать
    файл из режима 2 -- введите d, иначе -- ссылку.
    """)
    link = input('Введите: ')

    if link == 'd':
        videos_df = pd.DataFrame(second_mode('videos.json'))
    else:
        videos_df = pd.DataFrame(second_mode('link'))
    videos_list = list(zip(videos_df['channel'], videos_df['video'], videos_df['publish_date']))

    third_mode(videos_list)