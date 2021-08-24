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
import re
import pyinputplus as pyip
from twython import Twython
from pathlib import Path
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


with open('config.json') as config_file:
    config_values = json.load(config_file)

    DOWNLOADS_FOLDER = Path(config_values["DOWNLOADS_FOLDER"])  # Where your downloads are kept (Python needs this to retrieve files downloaded via javascript)
FILENAME_PARAMETERS = 'p5parameters.txt'    # Where p5js writes the parameters used
OUTPUT_FILE = Path('output.mp4')    # The final mp4 file that FFmpeg exports
IMAGE_FOLDER = Path('./imageSet')   # Folder where all the images from CCapture are found

START_TIME = 0


# Searches for a .tar file in the downloads folder that was created later than {start_time}.
def get_new_CCapture(newerThan, searchIn = DOWNLOADS_FOLDER):
    '''
    Input: 
        newerThan: a float object (usually from time.time()) that represents the oldest possible time that a .tar file can be
        searchIn: a Path object pointing to a directory you want to search for tar files

    Output: returns a Path object with the filename of a tar file which was created later than newerThan 
        if more than 1 tar file exists, it returns the one that comes first when arranged alphabetically
    '''
    for file in glob.glob(str(searchIn / '*.tar')):
        if os.path.getctime(file) >= newerThan:
            return Path(file)


def cleanup():
    '''
    Deletes the following:
        imageSet / *.png
        output.mp4
        p5parameters.txt
    '''
    for image in glob.glob(str(IMAGE_FOLDER / '*.png')):
        os.unlink(image)
    if os.path.exists(OUTPUT_FILE):
        os.unlink(OUTPUT_FILE)
    if os.path.exists(FILENAME_PARAMETERS):
        os.unlink(FILENAME_PARAMETERS)


def browser_generate():
    '''
    Output: a selenium WebDriver object that's configured to run headless and without download prompts
    '''
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")    # Disables the log messages from CCapture so I can put my own
    chrome_options.add_experimental_option("prefs", {
        "download.prompt_for_download": False,
    })
    d = DesiredCapabilities.CHROME
    d['goog:loggingPrefs'] = {'browser': 'ALL'}

    browser = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=chrome_options,
            desired_capabilities=d)
    browser.command_executor._commands["send_command"] = (
        "POST", '/session/$sessionId/chromium/send_command')

    params = {'cmd': 'Page.setDownloadBehavior', 'params': {
        'behavior': 'allow',
        'downloadPath': str(DOWNLOADS_FOLDER)}}
    browser.execute("send_command", params)
    return browser


def extract_tar(tar_from, folder_to=IMAGE_FOLDER, delete=False):
    '''
    Input:
        tar_from: Path object pointing to a tar file whose contents will be extracted to folder_to
        folder_to: Path object pointing to a destination directory where tar_from will be extracted to
        delete: boolean 
            True - deletes tar_from after extraction
            False - leaves tar_from intact
    '''
    tar_from = str(tar_from)
    tarFile = tarfile.open(tar_from)
    tarFile.extractall(IMAGE_FOLDER)
    tarFile.close()
    if delete:
        os.unlink(tar_from)


def regex_progress(to_search):
    '''
    Input: a str object that should indicate which frame is currently being recorded
        Format:  * "Full Frame! <current frame>" * 
    
    Output: an int object containing the frame we're currently rendering
    '''
    #  Exit automatically if CCapture is done
    if "Capturer stop" in to_search:
        return 900
    
    #  Find the current frame if it's not done yet
    try:
        frameRegex = re.compile(r'(Full Frame!|Frame:) (\d+)')
        current_frame = frameRegex.search(to_search).group(2)
        return int(current_frame)
    except:
        return 0    # BUG: Sometimes, python starts looking for "Full Frame! <number>" before CCapture has even begun rendering the first one so sometimes I read regular console logs. 
                    # This try-except catches that but it's an inelegant way of saying "I didn't render anything yet"


def main():
    START_TIME = time.time()
    if not os.path.exists(IMAGE_FOLDER):
        os.mkdir(IMAGE_FOLDER)

    browser = browser_generate()
    browser.get(os.path.abspath('p5js/index.html'))

    browser_log = 'Frame: 0'
    # Wait for CCapture to render a tar file will all the recorded images
    while not (current_frame := regex_progress(browser_log)) == 900:
        try:
            browser_log = browser.get_log('browser')[-1]['message']
        except IndexError:
            pass
        print(f'{current_frame} of 900', end='\r')    
        time.sleep(1)

    # Wait for the completed tar file to finish downloading
    while not (DOWNLOADED_TAR := get_new_CCapture(START_TIME)):
        time.sleep(1)
    browser.close()

    cleanup()   # Delete files that were generated from previous executions of automate.py

    extract_tar(tar_from=DOWNLOADED_TAR, folder_to=IMAGE_FOLDER, delete=True)   # Extract the contents of the .tar file into an image folder
    
    shutil.move(DOWNLOADS_FOLDER / FILENAME_PARAMETERS, FILENAME_PARAMETERS)
    print('Now generating mp4...')
    # Instruct FFMPEG to make an mp4 from the image set
    os.system("cmd /c ffmpeg -r 60 -f image2 -s 1280x720 -i " + str(Path(IMAGE_FOLDER) / '%07d.png')
              + " -vcodec libx264 -crf 17 -pix_fmt yuv420p " + str(OUTPUT_FILE))

    while not os.path.exists(OUTPUT_FILE):  # Wait for FFMPEG to finish
        time.sleep(1)

    os.startfile(OUTPUT_FILE)   # Automatically opens the rendered mp4 for viewing

    fparams = open(FILENAME_PARAMETERS, 'r', encoding='utf=8')
    params = fparams.read()
    fparams.close()
    print('\n\n' + params + '\n\n')
    print(f'Compilation finished in {time.time() - START_TIME} seconds.')


while True:
    try:
        main()
    except KeyboardInterrupt:   # I like to use a keyboard interrupt when I want to render a different pendulum
        print("Yikes, guess you didn't like that one")
    if pyip.inputYesNo("Do you want me to render a new video? ") == 'no':
        break
