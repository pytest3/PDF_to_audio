import boto3
import pdfplumber
from time import sleep
import requests
import os, sys, subprocess

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = 'practisebucketaws'
TOPIC_ARN = 'arn:aws:sns:ap-southeast-1:524255913858:audiobook'
region = 'ap-southeast-1'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 '
                        '(KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36'}

# Extract text from pdf
with pdfplumber.open('The Girl with the Dragon Tattoo.pdf') as pdf:
    all_pages = pdf.pages
    full_text = ''
    for page in all_pages:
        single_page_text = page.extract_text(x_tolerance=1)
        full_text = full_text + '\n' + single_page_text

# Create a boto3 session
polly_client = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                             region_name=region).client('polly')

# Request speech synthesis
response = polly_client.start_speech_synthesis_task(VoiceId='Joanna',
                                                    OutputS3BucketName=AWS_BUCKET_NAME,
                                                    OutputFormat='mp3',
                                                    Text=str(full_text),
                                                    SnsTopicArn=TOPIC_ARN,
                                                    Engine='neural')

# Get mp3 file uri from response
mp3_uri = response['SynthesisTask']['OutputUri']

# Wait for speech to be fully synthesisedd
retries = 0
max_retries = 30
still_try = True
while retries < max_retries and still_try == True:
    if requests.get(mp3_uri, headers=headers).status_code != 200:
        retries += 1
        print(f'mp3 file not ready..')
        sleep(60)
    else:
        print(f'mp3 file is ready..')
        audiobook = requests.get(mp3_uri, headers=headers)
        with open('audiobook.mp3', 'wb') as file:
            file.write(audiobook.content)
        still_try = False

# Play audiobook
if sys.platform == "win32":
    os.startfile('audiobook.mp3')
else:
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.call([opener, 'audiobook.mp3'])
