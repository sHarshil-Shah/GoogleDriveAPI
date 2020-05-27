# -*- coding: utf-8 -*-
"""
Created on Mon May 18 18:45:11 2020

@author: Sum
"""
from __future__ import print_function

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os, io
from apiclient.http import MediaFileUpload, MediaIoBaseDownload
from apiclient import errors
import httplib2
import json

with open('config.txt') as json_file:
    data = json.load(json_file)
    # print(data)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']
folder_name = data['folder_name'] #'DATA2020'
folder_path = data['path'] #r'E:\STUDY\Project\new'
creds = None
service = None
def main():
    global service, creds
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

def getfilesFromLocal():
    import glob
    folder_id, trashed = findFolder()
    if(folder_id is None or trashed):
        print("Folder %s not found" %folder_name)
        file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
        }
        file = service.files().create(body=file_metadata,
                                            fields='id, name').execute()
        
        folder_id = file.get('id')
        print ('Folder is Created: %s' % file.get('name'))
        
    count  = 0
    total_file_count = len(glob.glob(folder_path+r"\*"))
    for path in glob.glob(folder_path+r"\*"):
        count += 1
        uploadFile(os.path.basename(path), path, folder_id, total_file_count, count)
    print("Uploaded %d files" %count)
    

def uploadFile(filename,filepath, folder_id, total_file_count, count):
    file_metadata = {'name': filename, "parents": [folder_id]}
    media = MediaFileUpload(filepath)
    file = service.files().create(body=file_metadata, media_body=media, fields='id, name, size').execute()
    print ('Uploaded File : %20s   %15skb %4s of %s' % (file.get('name'), file.get('size'), count,  total_file_count))

def findFolder():
    page_token = None
    while True:
        response = service.files().list(q="mimeType='application/vnd.google-apps.folder'",
                                              spaces='drive',
                                              fields='nextPageToken, files(id, name, trashed)',
                                              pageToken=page_token).execute()
        for file in response.get('files', []):
            # Process change
            if(file.get('name') == folder_name):
                print ('Found Folder: %s ' % (file.get('name')))
                if(file.get('trashed')):
                    print("Folder is in Trash.")                
                return file.get('id'), file.get('trashed')     
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            return 


def download_files_in_folder():  
    folder_id, trashed = findFolder()
    global creds, service  
  
    if(trashed):
        print("Dwonloading Failed. Folder %s is in Trash. Please restore it by going to your drive https://drive.google.com/drive/ and then into 'Trash' in left Panel." %folder_name)
        return
  
    request = service.files().list(q = "'"+folder_id+"' in parents")
    count = 0
    while request is not None:
      response = request.execute()
      count = count + len(response.get('files'))
      request = service.files().list_next(request, response)
    total_files = count  
  
    request = service.files().list(q = "'"+folder_id+"' in parents")
    count = 0
    print("Downloading files from Google Drive...")
    while request is not None:
      response = request.execute()
      # print("Total files to be Downloaded: " + str(len(response.get('files'))))
      # print(response.get('files'))
      for r in response.get('files'):
          # print(r.get('name'))
          count = count + 1
          downloadFile(r.get('name'), r.get('id'), folder_path, total_files, count)
      # Do stuff with response['files']
      # 
      request = service.files().list_next(request, response)
    print("Downloading Done. \n Total Downloaded: " + str(count))
    
    
def downloadFile(file_name, file_id,filepath, total_files, count):
    import os
    
    if not os.path.exists(filepath):
        import subprocess
        subprocess.call(['chmod', '-R', '+w', filepath])
        print("Path is created")
    
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        try:
            status, done = downloader.next_chunk()
            print("Downloaded: "+ '%20s  %4s of %s' % (file_name,  count,  total_files))#+" %d%%." % int(status.progress() * 100))
        except errors.HttpError:
            # done = True
            print("Error While Downloading: " + file_name)
    with io.open(filepath+'\\'+file_name,'wb') as f:
        fh.seek(0)
        f.write(fh.read())

if __name__ == '__main__':
    try:
        main()
        p = int(input("Press \n 1 for Uploading Backup \n 2 for Downloading Backup \n"))
         
        def uploadFiles():
            getfilesFromLocal()     
            
        def downloadFiles():
            download_files_in_folder()
         
        switcher = {
                1: uploadFiles,
                2: downloadFiles
            }
         
        def choice(argument):
            # Get the function from switcher dictionary
            func = switcher.get(argument, "nothing")
            # Execute the function
            return func()
        
        choice(p) 
    except httplib2.ServerNotFoundError:
        print("Check Internet Connection")