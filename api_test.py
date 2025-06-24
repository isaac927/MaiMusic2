import os
import time
import shutil
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Authenticate with Google Drive
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

INPUT_FOLDER_NAME = 'spleeter_input'
OUTPUT_FOLDER_NAME = 'spleeter_output'

def get_folder_id(name):
    file_list = drive.ListFile({'q': "mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
    for file in file_list:
        if file['title'] == name:
            return file['id']
    return None

def upload_audio(file_path):
    folder_id = get_folder_id(INPUT_FOLDER_NAME)
    if not folder_id:
        raise Exception("Input folder not found on Drive.")

    file_name = os.path.basename(file_path)
    gfile = drive.CreateFile({'parents': [{'id': folder_id}], 'title': file_name})
    gfile.SetContentFile(file_path)
    gfile.Upload()
    print(f"Uploaded {file_name} to Drive.")

def download_results(stem_name, destination_folder="."):
    folder_id = get_folder_id(OUTPUT_FOLDER_NAME)
    if not folder_id:
        raise Exception("Output folder not found on Drive.")

    result_files = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
    for file in result_files:
        if file['title'].startswith(stem_name):
            file.GetContentFile(os.path.join(destination_folder, file['title']))
            print(f"Downloaded: {file['title']}")

# Example usage
upload_audio("input/sample3.mp3")  # Path to your audio file
print("Waiting for separation to finish...")
time.sleep(90)  # Give Colab time to process (adjust depending on song length)
download_results("test_song")  # stem name (no extension)