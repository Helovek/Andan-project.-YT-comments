
import time
import json
from googleapiclient.discovery import build

api_key = "AIzaSyBcH24rIhGpB1Z4zhVi2Cx-mTdK0K7WvIg"


def get(video_id):
    youtube = build("youtube", "v3", developerKey=api_key)

    comments = []
    next_page_token = None

    while True:
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=100,
            textFormat='plainText',
            pageToken=next_page_token
        )
        response = request.execute() # make request to google

        for i in response.get("items", []):
            snippet = i['snippet']['topLevelComment']['snippet'] # извлекаем комментарий из ветки
            comment_data = {
                'user': i['snippet']['topLevelComment']['id'],
                'data&time': snippet['publishedAt'],
                'text': snippet['textDisplay']
            }
            comments.append(comment_data)
        next_page_token = response.get("nextPageToken")

        # выходим из while, если комментарии закончились
        if not next_page_token: break
        time.sleep(0.5)

    return comments