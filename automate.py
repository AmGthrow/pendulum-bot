'''
    automate.py - generates an mp4 file with the double pendulum video I want to upload, as well as a text file with the pendulum's
    parameters written into it
'''
import os, shutil, time, glob, tarfile, sys, posttweet
import pyinputplus as pyip
from twython import Twython
from pathlib import Path
from selenium import webdriver


DOWNLOADS_FOLDER = Path(r'C:\Users\jsmod\Downloads') # Point this to wherever your browser downloads files. This is where python accesses the files generated from p5js


# os.chdir(os.path.dirname(sys.argv[0]))  # Just to make sure that the working dirctory is where this script is located

START_TIME = time.time()
FILENAME_PARAMETERS = 'p5parameters.txt'    # Where p5js writes the parameters used

OUTPUT_FILE = Path('output.mp4')    # The final mp4 file that FFmpeg exports
IMAGE_FOLDER = Path('./imageSet')   # Folder where all the images from CCapture are found

def get_new_CCapture(): # Searches for a .tar file in the downloads folder that was created later than {start_time}.
                        # This should be the .tar file that you create upon running this script
    for file in glob.glob(str(DOWNLOADS_FOLDER / '*.tar')):
        if os.path.getctime(file) >= START_TIME:
            return file

def main():
    if not os.path.exists(IMAGE_FOLDER):
        os.mkdir(IMAGE_FOLDER)

    # Delete old image sets, txt files, and mp4 files before proceeding
    if os.path.exists(OUTPUT_FILE):
        os.unlink(OUTPUT_FILE)
    if os.path.exists(FILENAME_PARAMETERS):
        os.unlink(FILENAME_PARAMETERS)
    for image in os.listdir(IMAGE_FOLDER):
        os.unlink(IMAGE_FOLDER / image)

    browser = webdriver.Chrome()
    browser.get(os.path.abspath('p5js/index.html'))   #NOTE: CCapture starts by itself, so there's no need to manually start recording in the python file

    # Moves the p5parameters.txt file from your downloads to this scripts directory; just for organization
    while not os.path.exists(DOWNLOADS_FOLDER / FILENAME_PARAMETERS):
        time.sleep(1)
    shutil.move(DOWNLOADS_FOLDER / FILENAME_PARAMETERS, FILENAME_PARAMETERS)

    while not get_new_CCapture():   # Wait for CCapture to download the tar file will all the recorded images
        time.sleep(1)
    browser.close()


    # Extract the contents of the .tar file into an image folder
    DOWNLOADED_TAR = get_new_CCapture()
    tarFile = tarfile.open(DOWNLOADED_TAR)
    tarFile.extractall(IMAGE_FOLDER)
    tarFile.close()
    os.unlink(DOWNLOADED_TAR)


    print('Now generating mp4...')
    # Instruct CCapture to make an mp4 from the image set
    os.system("cmd /c ffmpeg -r 60 -f image2 -s 1280x720 -i " + str(Path(IMAGE_FOLDER) / '%07d.png') \
            + " -vcodec libx264 -crf 17 -pix_fmt yuv420p " + str(OUTPUT_FILE))

    while not os.path.exists(OUTPUT_FILE):
        time.sleep(1)

    os.startfile(OUTPUT_FILE)   # I like to to view the video before proceeding
    print(f'Compilation finished in {time.time() - START_TIME} seconds.')



while True:   # Sometimes I have an output file that's ready to go so I just tweet that
    try:
        main()
    except KeyboardInterrupt:   # I like to use a keyboard interrupt when I want to try rendering a different pendulum
        print("Yikes, guess you didn't like that one")
    if pyip.inputYesNo("Do you want me to render a new video? ") == 'no':
        break

