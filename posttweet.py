''' 
    posttweet.py - tweets the mp4 file that was generated using automate.py
'''
from pathlib import Path
from twython import Twython
import sys, os, json

config_file = open('config.json')
config_values = json.load(config_file)


os.chdir(os.path.dirname(sys.argv[0]))   # Make sure that we're operating where the script actually is

FILENAME_PARAMETERS = 'p5parameters.txt'    # Where p5js writes the parameters used
OUTPUT_FILE = Path('output.mp4')    # The final mp4 file that FFmpeg exports
IMAGE_FOLDER = Path('./imageSet')   # Folder where all the images from CCapture are found   

def tweet():
    # Capture the parameters used in the p5 sketch. This is the text I'm going to tweet
    try:
        parameters = open(FILENAME_PARAMETERS, 'r', encoding='utf-8')
        video = open(OUTPUT_FILE, 'rb')
        message = parameters.read()
        parameters.close()
    except FileNotFoundError:
        print("Couldn't find an existing output. Try running automate.py first.\n\nNo longer sending tweet...")
        exit()
    print(message)

    twitter = Twython(config_values["CONSUMER_KEY"], config_values["CONSUMER_SECRET"], config_values["API_KEY"], config_values["API_SECRET"])

    response = twitter.upload_video(media=video,media_type='video/mp4')
    twitter.update_status(status=message, media_ids=[response['media_id']])
    print("It's uploaded!")

if __name__ == "__main__":
    tweet()
