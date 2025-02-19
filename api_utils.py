from dotenv import load_dotenv
import os
import requests
import config
import re
import math
import random
import tweepy
import time
import logging

load_dotenv()

# X API Key
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
APIFY_API_KEY = os.getenv("APIFY_API_KEY")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
UPLOAD_URL = 'https://api.x.com/2/media/upload'

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_twitter_trend():
    """Fetch trending topics from Apify's Twitter Trends Scraper, sort by tweet volume, and pick one randomly"""
    url = f"https://api.apify.com/v2/actor-tasks/assuring_fade~twitter-trends-scraper/run-sync-get-dataset-items?token={APIFY_API_KEY}"
    
    response = requests.get(url)

    if 200 <= response.status_code < 300:
        trends = response.json()

        # Convert volume strings (e.g., "11,200Tweets") to integers
        for trend in trends:
            volume_str = re.sub(r"\D", "", trend["volume"])
            trend["volume_int"] = int(volume_str) if volume_str else 0

        # Sort trends by tweet volume in descending order
        sorted_trends = sorted(trends, key=lambda x: x["volume_int"], reverse=True)

        # Extract top 5 trending topics
        top_trends = [t["trend"] for t in sorted_trends[:5]]

        # Randomly pick one from the top 5
        selected_trend = random.choice(top_trends) if top_trends else "memes"
        
        return selected_trend
    else:
        print("Error fetching trends:", response.json())
        return "memes"  # Default trend if API fails

def get_twitter_tones(trend):
    """Fetch tweets from Apify's Tweet Scraper using a specific trend and extract tweet texts."""
    url = f"https://api.apify.com/v2/actor-tasks/assuring_fade~tweet-scraper/run-sync-get-dataset-items?token={APIFY_API_KEY}"
    
    # Define the payload with the trend added to searchTerms
    payload = {
        "filter:blue_verified": False,
        "filter:consumer_video": False,
        "filter:has_engagement": False,
        "filter:hashtags": False,
        "filter:images": False,
        "filter:links": False,
        "filter:media": False,
        "filter:mentions": False,
        "filter:native_video": False,
        "filter:nativeretweets": False,
        "filter:news": False,
        "filter:pro_video": False,
        "filter:quote": False,
        "filter:replies": False,
        "filter:safe": False,
        "filter:spaces": False,
        "filter:twimg": False,
        "filter:verified": False,
        "filter:videos": False,
        "filter:vine": False,
        "include:nativeretweets": False,
        "maxItems": 5,
        "queryType": "Top",
        "searchTerms": [trend]  # Insert the trend here
    }

    response = requests.post(url, json=payload)

    if 200 <= response.status_code < 300:
        tweets = response.json()

        # Extract the text of each tweet
        tweet_texts = [tweet["text"] for tweet in tweets if "text" in tweet]

        return tweet_texts
    else:
        print("Error fetching tweets:", response.json())
        return []

def download_random_giphy_clip(topic):
    url = f"https://api.giphy.com/v1/clips/search?api_key={GIPHY_API_KEY}&q={topic}&limit=50&lang=en"
    response = requests.get(url)
    if 200 <= response.status_code < 300:
        results = response.json().get("data", [])
        if results:
            random_clip = random.choice(results)  # Pick a random MP4
            mp4_url = random_clip["images"].get("original_mp4", {}).get("mp4")  # Get MP4 version
            
            if mp4_url:
                clip_path = f"D:/Folder/Subfolder/{topic}_clip.mp4"  # Save in specific directory
                video_data = requests.get(mp4_url).content
                with open(clip_path, "wb") as file:
                    file.write(video_data)
                return clip_path  # Return full path
    print("Error fetching from Giphy or no MP4 available.")
    return None

def download_random_giphy_gif(topic):
    url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={topic}&limit=50&lang=en"
    response = requests.get(url)

    if 200 <= response.status_code < 300:
        results = response.json().get("data", [])
        if results:
            random_clip = random.choice(results)  # Pick a random gif
            gif_url = random_clip["images"].get("original", {}).get("url")  # Get gif version
            
            if gif_url:
                gif_path = f"D:/Folder/Subfolder/{topic}_gif.gif"
                gif_data = requests.get(gif_url).content
                with open(gif_path, "wb") as file:
                    file.write(gif_data)
                return gif_path  # Return full path

    print(response.status_code)
    print("Error fetching from Giphy or no Gif available.")
    return None

def generate_ai_caption(current_trend,tone):
    """Generate an AI-based caption using Groq API with separate system and user prompts."""
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": config.SYSTEM_PROMPT_CAPTION},
            {"role": "user", "content": f"Generate a 50 to 233 characters (special characters like punctuations or japanese alphabet are treated like a normal english letter in character count) tweet caption based on this topic: {current_trend}. You can refer to these top tweets for the current public sentiment and the general context/consensus of the topic: {tone}"}
        ]
    }

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)

    if 200 <= response.status_code < 300:
        caption = response.json()["choices"][0]["message"]["content"]
        caption = caption.strip('"')
        return caption
    else:
        print("Error:", response.json())
        return "Error generating caption"

def generate_topic_from_caption(caption):
    """Use Groq API to extract a general topic from the trending topic."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": config.SYSTEM_PROMPT_TOPIC},
            {"role": "user", "content": f"Generate a topic based on this caption: {caption}"}
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    if 200 <= response.status_code < 300:
        return response.json()["choices"][0]["message"]["content"].strip().lower()
    else:
        print("Error generating topic:", response.json())
        return "funny"  # Default topic

def init_upload(file_path, access_token):
    """Step 1: INIT - Request a media ID for upload"""
    file_size = os.path.getsize(file_path)

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    if file_path.lower().endswith(".mp4"):
        request_data = {
            'command': 'INIT',
            'media_type': 'video/mp4',
            'total_bytes': file_size,
            'media_category': 'amplify_video',
        }
    elif file_path.lower().endswith(".gif"):
        request_data = {
            'command': 'INIT',
            'media_type': 'image/gif',
            'total_bytes': file_size,
            'media_category': 'tweet_gif',
        }
    else:
        raise ValueError("Unsupported file type. Only MP4 and GIF are allowed.")

    response = requests.post(UPLOAD_URL, headers=headers, params=request_data)

    if response.status_code == 202:
        media_id = response.json().get("data", {}).get("id")
        print(f"✅ INIT success! Media ID: {media_id}")
        return media_id
    else:
        print("❌ INIT failed:", response.json())
        return None

def append_upload(file_path, media_id, access_token, chunk_size=3 * 1024 * 1024):
    """Step 2: APPEND - Upload file chunks to X API."""
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    file_size = os.path.getsize(file_path)
    segment_id = 0
    bytes_sent = 0

    with open(file_path, "rb") as f:
        while bytes_sent < file_size:
            chunk = f.read(chunk_size)

            files = {'media': ('chunk', chunk, 'application/octet-stream')}

            data = {
                "command": "APPEND",
                "media_id": media_id,
                "segment_index": segment_id,
            }

            response = requests.post(UPLOAD_URL, data=data,headers=headers, files=files)

            if response.status_code != 204:
                print(f"❌ APPEND failed: {response.json()}")
                return False

            segment_id += 1
            bytes_sent = f.tell()

            print(f'{bytes_sent} bytes uploaded')

    print("✅ All chunks uploaded successfully!")
    return True

def check_status(media_id, processing_info, access_token):
    """Checks video processing status for Twitter/X API using a loop."""

    retries=0

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    while retries<30:
        state = processing_info.get('state')
        print(f'Media processing status: {state}')

        if state == 'succeeded':
            return media_id

        if state == 'failed':
            print("❌ Media processing failed.")
            exit(0)

        check_after_secs = processing_info.get('check_after_secs', 10)  # Default 10s if missing
        percentage = processing_info.get('percentage', 0) # Default 0% if missing

        print(f'Checking after {check_after_secs} seconds..., currently {percentage}%')
        time.sleep(check_after_secs)

        # Request new status
        request_params = {
            'command': 'STATUS',
            'media_id': media_id
        }

        response = requests.get(url=UPLOAD_URL, params=request_params, headers=headers)

        # Handle request failures
        if response.status_code == 200:
            processing_info = response.json().get("data", {}).get("processing_info")
        elif response.status_code == 404:
            print("❌ Error: Media not found. Check if the media ID is correct or if the upload completed successfully.")
            processing_info = None
        elif response.status_code == 401:
            print("❌ Error: Unauthorized request. Check your authentication (access token may be expired).")
            processing_info = None
        else:
            print(f"❌ Unexpected error {response.status_code}: {response.text}")
            processing_info = None

        retries+=1

def finalize_upload(media_id, access_token):
    """Step 3: FINALIZE - Complete the upload"""
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    request_data = {
        'command': 'FINALIZE',
        'media_id': media_id,
    }

    response = requests.post(UPLOAD_URL, headers=headers, params=request_data)
    processing_info = response.json().get('data',{}).get('processing_info',{})

    return check_status(media_id,processing_info,access_token)

def upload_media(file_path, access_token):
    """Full upload process"""
    media_id = init_upload(file_path, access_token)
    if not media_id:
        return None

    print('✅ Init Success')

    success = append_upload(file_path, media_id, access_token)
    if not success:
        return None

    print('✅ Append Success')

    finalize = finalize_upload(media_id, access_token)
    print(finalize)
    return finalize

def create_tweet_payload(caption, media_id=None):
    # Start building the payload with the required fields
    payload = {
        "for_super_followers_only": False,
        "nullcast": False,
        "text": caption
    }
    
    # If media_id is provided, add the media key to the payload
    if media_id:
        payload["media"] = {
            "media_ids": [media_id]
        }

    return payload

def post_tweet(access_token_for_app):
    # URL for posting a tweet
    url = 'https://api.twitter.com/2/tweets'

    # Headers for authentication and content type
    headers = {
        'Authorization': f'Bearer {access_token_for_app}',
        'Content-Type': 'application/json'
    }

    # Get trending topic and tone (assuming you have implemented these functions)
    trend = get_twitter_trend()
    tone = get_twitter_tones(trend)
    caption = generate_ai_caption(trend, tone)
    topic = generate_topic_from_caption(caption)

    # Log the retrieved data
    logging.info(f"Trend: {trend}")
    logging.info(f"Tone: {tone}")
    logging.info(f"Topic: {topic}")

    media_function = random.choice([
        download_random_giphy_gif,
        download_random_giphy_clip,
        lambda x: None  # Function that returns None
    ])

    logging.info(f"Media function: {media_function}")

    media_file = media_function(topic)
    
    if media_file:
        media_id = upload_media(media_file,access_token_for_app)
    else:
        media_id = None

    payload = create_tweet_payload(caption=caption, media_id=media_id)

    response = requests.request("POST", url, json=payload, headers=headers)

    # Check if the tweet was posted successfully
    if response.status_code == 201:
        print(f"✅ Tweet posted: {caption}")
        logging.info(f"Tweet posted: {caption}")
    else:
        print(f"❌ Failed to post tweet. Status code: {response.status_code}")
        logging.info(f"Caption: {caption}")
        logging.error(f"Failed to post tweet. Status code: {response.status_code}")
        logging.error(f"Response: {response.json()}")
        print(response.json())