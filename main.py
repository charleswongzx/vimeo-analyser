import requests
import subprocess
import os
import shutil
import pandas as pd
import google_local

video_list = []


file = open('vimeo_token', 'r')
token = file.read().strip()
file.close()

headers = {'Authorization': 'Bearer ' + token}
video_ID = 1


for i in range(3):
    params = {'page': i+1,
          'per_page': 100}

    response = requests.get('https://api.vimeo.com/me/videos', headers=headers, params=params)
    videos_json = response.json()

    # for i in range(len(videos_json['data']))
    for listing in videos_json['data']:

        # EXTRACTING VIDEO
        url = listing['link']
        print(url)
        vid_name = listing['name']
        vid_name = vid_name.replace('/', '_')

        new_dir = 'Transcriptions/' + str(video_ID) + '_' + vid_name
        print new_dir
        try:
            os.mkdir(new_dir)
        except:

            pass

        # VIDEO TO FLAC
        cd = 'cd "' + new_dir + '"'
        subprocess.call(cd + "; youtube-dl -u 'adam@boost.vc' -p 'video12' -x --audio-format 'flac' " + url, shell=True)

        clips = os.listdir(new_dir)
        new_file_path = clips[0].replace('.flac', '_single.flac')
        subprocess.call(cd + "; ffmpeg -i '" + clips[0] + "' -ac 1 -filter:a 'volume=2.0' '" + new_file_path + "'" + "; rm '" + clips[0] + "'", shell=True)
        audio_path = new_dir + '/' + new_file_path

        # UPLOAD FLAC TO GOOGLE CLOUD BUCKET
        print 'Uploading to GS...'
        gs_uri = google_local.upload_to_cloud('boost-vc-audio', new_dir + '/' + new_file_path)

        # TRANSCRIBE AND SAVE LOCALLY
        print 'Transcribing audio...'
        transcription = google_local.transcribe(gs_uri)
        transcription_path = new_dir + '/' + new_file_path.replace('.flac', '.txt')
        txt_file = open(transcription_path, 'w')
        txt_file.write(transcription)
        txt_file.close()

        # UPLOAD FLAC AND TRANSCRIPTION TO GOOGLE DRIVE

        audio_url, sub_folder_id = google_local.upload_to_gdrive('1defofalUgX1NcIxHNQ899-yfOvLGkYHO', audio_path, str(video_ID) + '_' + vid_name,  new_file_path, 'audio/flac')
        transcription_url, sub_folder_id = google_local.upload_to_gdrive(sub_folder_id, transcription_path, str(video_ID) + '_' + vid_name, new_file_path.replace('.flac', '.txt'), 'text/markdown', listing_exists=True)

        csv_listing = {'VideoID': video_ID, 'VideoName': vid_name, 'VideoLink': url, 'AudioLink': audio_url, 'TranscriptionLink': transcription_url, 'Tags': '', 'Source': 'BoostVC'}
        video_list.append(csv_listing)

        shutil.rmtree(new_dir, ignore_errors=True)
        video_ID += 1

df = pd.DataFrame(video_list)
df.to_csv('Data/boost_video_vimeo.csv')
