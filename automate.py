'''
    automate.py - generates an mp4 file with the double pendulum video I want to upload, as well as a text file with the pendulum's
    parameters written into it
'''
import os
import shutil
import time
import glob
import tarfile
import sys
import posttweet
import json
import pyinputplus as pyip
from twython import Twython
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


config_file = open('config.json')
config_values = json.load(config_file)

DOWNLOADS_FOLDER = Path(config_values["DOWNLOADS_FOLDER"])  # Where your downloads are kept (Python needs this to retrieve files downloaded via javascript)
config_file.close()


FILENAME_PARAMETERS = 'p5parameters.txt'    # Where p5js writes the parameters used
OUTPUT_FILE = Path('output.mp4')    # The final mp4 file that FFmpeg exports
IMAGE_FOLDER = Path('./imageSet')   # Folder where all the images from CCapture are found



# Searches for a .tar file in the downloads folder that was created later than {start_time}.
def get_new_CCapture(newerThan, searchIn = DOWNLOADS_FOLDER):
    '''
    Input: 
        newerThan: a float object (usually from time.time()) that represents the oldest possible time that a .tar file can be
        searchIn: a Path object pointing to a directory you want to search for tar files

    Output: returns a str object with the filename of a tar file which was created later than newerThan 
        if more than 1 tar file exists, it returns the one that comes first when arranged alphabetically
    '''
    for file in glob.glob(str(searchIn / '*.tar')):
        if os.path.getctime(file) >= newerThan:
            return file


def cleanup():
    # Delete old image sets
    for image in os.listdir(IMAGE_FOLDER):
        os.unlink(IMAGE_FOLDER / image)

    # delete the previous output.mp4 and p5parameters.txt before putting new ones into the working directory
    if os.path.exists(OUTPUT_FILE):
        os.unlink(OUTPUT_FILE)
    if os.path.exists(FILENAME_PARAMETERS):
        os.unlink(FILENAME_PARAMETERS)

def browser_options():
    '''
    Output: an
    '''
def main():
    START_TIME = time.time()
    if not os.path.exists(IMAGE_FOLDER):
        os.mkdir(IMAGE_FOLDER)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_experimental_option("prefs", {
        "download.prompt_for_download": False,
    })
    chrome_driver = os.path.abspath("chromedriver.exe")
    browser = webdriver.Chrome(
        options=chrome_options, executable_path=chrome_driver)
    browser.command_executor._commands["send_command"] = (
        "POST", '/session/$sessionId/chromium/send_command')

    params = {'cmd': 'Page.setDownloadBehavior', 'params': {
        'behavior': 'allow',
        'downloadPath': str(DOWNLOADS_FOLDER)}}
    browser.execute("send_command", params)

    browser.get(os.path.abspath('p5js/index.html'))

    while not (DOWNLOADED_TAR := get_new_CCapture(START_TIME)):   # Wait for CCapture to download the tar file will all the recorded images
        time.sleep(1)
    browser.close()

    # Extract the contents of the .tar file into an image folder
    tarFile = tarfile.open(DOWNLOADED_TAR)
    tarFile.extractall(IMAGE_FOLDER)
    tarFile.close()
    os.unlink(DOWNLOADED_TAR)

    print('Now generating mp4...')
    # Instruct CCapture to make an mp4 from the image set
    os.system("cmd /c ffmpeg -r 60 -f image2 -s 1280x720 -i " + str(Path(IMAGE_FOLDER) / '%07d.png')
              + " -vcodec libx264 -crf 17 -pix_fmt yuv420p " + str(OUTPUT_FILE))

    while not os.path.exists(OUTPUT_FILE):
        time.sleep(1)
    shutil.move(DOWNLOADS_FOLDER / FILENAME_PARAMETERS, FILENAME_PARAMETERS)

    os.startfile(OUTPUT_FILE)   # I like to to view the video before proceeding
    params = open(DOWNLOADS_FOLDER / FILENAME_PARAMETERS,
                  'r', encoding='utf=8').read()
    print('\n\n' + params + '\n\n')
    print(f'Compilation finished in {time.time() - START_TIME} seconds.')


while True:
    try:
        main()
    except KeyboardInterrupt:   # I like to use a keyboard interrupt when I want to render a different pendulum
        print("Yikes, guess you didn't like that one")
    if pyip.inputYesNo("Do you want me to render a new video? ", default="no", timeout=120) == 'no':
        break
