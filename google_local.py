import io
import os
import glob

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from google.cloud import storage

from googleapiclient.discovery import build, MediaFileUpload
from httplib2 import Http
from oauth2client import client, tools
from oauth2client import file as g_file


def upload_to_cloud(bucket_id, filename):
    client = storage.Client()
    bucket = client.get_bucket(bucket_id)

    blob = bucket.blob(filename)
    blob.upload_from_filename(filename)
    print filename, 'upload successful'

    return 'gs://' + bucket_id + '/' + filename


def transcribe(gs_uri):
    # Instantiates a client
    client = speech.SpeechClient()
    audio = types.RecognitionAudio(
        uri=gs_uri
    )
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=48000,
        language_code='en-US')

    # Detects speech in the audio file
    operation = client.long_running_recognize(config, audio)
    response = operation.result()
    transcription = ''

    for result in response.results:
        transcription += result.alternatives[0].transcript
        print('Transcript: {}'.format(result.alternatives[0].transcript))

    return transcription


def upload_to_gdrive(g_folder_id, filename, target_path, target_name, mimetype, listing_exists=False):
    SCOPES = 'https://www.googleapis.com/auth/drive'

    target_folder_id = g_folder_id

    store = g_file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('drive_credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('drive', 'v3', http=creds.authorize(Http()))

    if listing_exists == False:
        # CREATE TARGET FOLDER
        file_metadata = {
            'name': target_path,
            'parents': [g_folder_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        file = service.files().create(body=file_metadata,
                                      fields='id').execute()
        target_folder_id = file.get('id')
        print 'Folder ID: %s' % target_folder_id

    file_metadata = {'name': target_name,
                     'parents': [target_folder_id]}
    media = MediaFileUpload(filename,
                            mimetype=mimetype)
    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id').execute()
    print 'File ID: %s' % file.get('id')
    return 'https://drive.google.com/file/d/' + file.get('id'), target_folder_id

# print upload_to_cloud('boost-vc-audio', 'README.md')

