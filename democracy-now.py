#!/usr/bin/env python3
# <a rel="me" href="https://disobey.net/@DemocracyNow">Mastodon</a>

import os
import sys
import urllib.request
import feedparser
import mastodon
import html
import re
from datetime import datetime

# Set the base Mastodon URL
MASTODON_URL = "https://disobey.net"

MEDIA_BASE_URL = "https://media.disobey.net"

# Set the media directory location on the media server
MEDIA_DIR = "/var/www/media"

# Set the Democracy Now podcast XML feed URLs
AUDIO_FEED_URL = "https://www.democracynow.org/podcast.xml"
VIDEO_FEED_URL = "https://www.democracynow.org/podcast-video.xml"

# Parse command line arguments
force_run = False
if len(sys.argv) > 1 and sys.argv[1] == '-f':
    force_run = True

# Get the current date in YYYY-MM-DD format
CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')

# Set up the Mastodon API client with a bearer token
mastodon_api = mastodon.Mastodon(
    api_base_url=MASTODON_URL,
    access_token='ACCESS_TOKEN_HERE'
)

# Download the audio and video files
audio_feed = feedparser.parse(AUDIO_FEED_URL)
video_feed = feedparser.parse(VIDEO_FEED_URL)

latest_audio_file = None
latest_video_file = None
latest_date = None
for entry in audio_feed.entries + video_feed.entries:
    date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z').strftime('%Y-%m-%d')
    if date == CURRENT_DATE:
        audio_enclosures = [e for e in entry.enclosures if e.type.startswith('audio/')]
        video_enclosures = [e for e in entry.enclosures if e.type.startswith('video/')]

        if audio_enclosures:
            audio_url = audio_enclosures[0].href
            audio_file = os.path.basename(audio_url)
            audio_local_path = os.path.join(MEDIA_DIR, audio_file)
            if not os.path.exists(audio_local_path):
                urllib.request.urlretrieve(audio_url, audio_local_path)
            latest_audio_file = audio_file

        if video_enclosures:
            video_url = video_enclosures[0].href
            video_file = os.path.basename(video_url)
            video_local_path = os.path.join(MEDIA_DIR, video_file)
            if not os.path.exists(video_local_path):
                urllib.request.urlretrieve(video_url, video_local_path)
            latest_video_file = video_file

        # Store the latest date
        latest_date = date

# If there is a new episode, post to Mastodon
if force_run or (latest_date is not None and latest_date != previous_date):

    # Convert the latest_date to a datetime object
    latest_date = datetime.strptime(latest_date, '%Y-%m-%d')

    # Construct the status message
    summary = html.unescape(audio_feed.entries[0].summary)
    summary = re.sub(r'<[^>]+>', '', summary)  # remove HTML tags
    summary = re.sub(r'&\w+;', '', summary)  # remove HTML entities
    summary = re.sub(r'; ', ';\n\n', summary)  # add new line after each headline
    summary = re.sub(r'^\n+', '', summary)  # remove extra new lines
    status_message = f"{summary.strip()}\n\n"

    if latest_audio_file:
        audio_url = f"{MEDIA_BASE_URL}/{latest_audio_file}"
        status_message += f"Audio: {audio_url}\n\n"

    if latest_video_file:
        video_url = f"{MEDIA_BASE_URL}/{latest_video_file}"
        status_message += f"Video: {video_url}\n\n"

    # Add hashtags to the end of the status message
    status_message += "#DemocracyNow #News"

    # Post to Mastodon
    mastodon_api.status_post(status_message)
