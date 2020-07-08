''' 
    posttweet.py - tweets the mp4 file that I generated using automate.py
'''
from pathlib import Path
from twython import Twython
import sys, os

API_KEYS = Path(r'C:\Users\Jethro\Desktop\twitterAPI.txt')    # Obviously I can't use my real API keys here, so I have an external txt file with all my keys


os.chdir(os.path.dirname(sys.argv[0]))   # Make sure that we're operating where the script actually is

FILENAME_PARAMETERS = 'p5parameters.txt'    # Where p5js writes the parameters used
OUTPUT_FILE = Path('output.mp4')    # The final mp4 file that FFmpeg exports
IMAGE_FOLDER = Path('./imageSet')   # Folder where all the images from CCapture are found   

def tweet():
    # Capture the parameters used in the p5 sketch. This is the text I'm going to tweet
    parameters = open(FILENAME_PARAMETERS, 'r', encoding='utf-8')
    message = parameters.read()
    parameters.close()
    print(message)

    # Retrieve the actual keys from API_KEYS
    keysFile = open(API_KEYS, 'r')
    keysList = keysFile.read().splitlines() 
    keysFile.close()

    twitter = Twython(keysList[0], keysList[1], keysList[2], keysList[3])

    video = open(OUTPUT_FILE, 'rb')
    response = twitter.upload_video(media=video,media_type='video/mp4')
    twitter.update_status(status=message, media_ids=[response['media_id']])
    print("It's uploaded!")

if __name__ == "__main__":
    tweet()
