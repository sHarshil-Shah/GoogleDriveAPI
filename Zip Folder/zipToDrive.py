from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os, io
from apiclient.http import MediaFileUpload, MediaIoBaseDownload
import httplib2
import json
import zipfile
from apiclient import errors
from datetime import datetime
import shutil

with open('configuration.txt') as json_file:
    configList = json.load(json_file)

SCOPES = ['https://www.googleapis.com/auth/drive']
folder_name = configList.get('folder_name')     # "folder_name": "DATA2020"
directory = configList.get('folder_path') # "directory":  "E:\\STUDY\\Project\\zipdownload"
folder_absolute_path = directory + '\\' + folder_name # "E:\\STUDY\\Project\\zipdownload\\DATA2020"
zip_path = configList.get('zip_path')
zip_name = folder_name + '.zip'
zip_absolute_path = zip_path + '\\' + zip_name 

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

def folderToZip():
    print("Zipping Folder from " + folder_absolute_path)
    shutil.make_archive(zip_path+'\\'+folder_name , 'zip', folder_absolute_path)   
    
    #zipf = zipfile.ZipFile(zip_absolute_path, 'w', zipfile.ZIP_DEFLATED)
    #for root, dirs, files in os.walk(folder_absolute_path):
    #    print("\tTotal files: " + str(len(files)))
    #    for file in files:
    #        zipf.write(os.path.join(root, file))
    #        print("os.path.join(root, file)")
    #zipf.close()
    
    print("Zipping Done.\n")

def uploadFile(filename,filepath, mimeType): # zip file name, zip file path
    folderToZip()
    oldZipFiles = getZipId()
    file_metadata = {'name': filename,  'createdTime': 'T'.join(str(datetime.now()).split('.')[0].split(" "))+".365Z"}
    try:
        print("Uploading latest file...")
        media = MediaFileUpload(filepath, mimetype=mimeType)
        file = service.files().create(body=file_metadata, media_body=media, fields='id, name, size, createdTime').execute()
        print ('Uploaded File : %20s   %12.2f MB' % (file.get('name'), int(file.get('size'))/1000000))
        
        try:
            print("\nDeleting Old Zip files from Drive")
            for zip_id in oldZipFiles:
                deleteFile(zip_id)
            print("Successfully removed Old Zip backups from Drive.\n")
        except TypeError:
            pass
        finally:
            print("\nUpload Successful.\n")
        os.remove(filepath)
    except FileNotFoundError:
        print("File Not found at %s" % (filepath))       
    except PermissionError:
        pass
    
def getZipId():
    page_token = None
    zipIdList = []
    while True:
        response = service.files().list(q="mimeType='application/zip'",
                                              spaces='drive',
                                              fields='nextPageToken, files(id, name, createdTime, modifiedTime)',
                                               pageToken=page_token).execute()
        # print ('%11s %s %s' % ('', 'File Name'.center(20), 'Upload Date'.center(33)))
        for file in response.get('files', []):
            if(file.get('name') == zip_name):                
                # print ('Zip Found: %-20s %s' % (file.get('name'), datetime.strptime(file.get('createdTime')[:-5], '%Y-%m-%dT%H:%M:%S')))
                zipIdList.append(file.get('id'))
                # return file.get('id'), file.get('trashed')     
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            # print(zipIdList)
            print()
            return zipIdList 
        
def deleteAllFilesWithSpecificName():
    page_token = None
    while True:
        response = service.files().list(spaces='drive',
                                              fields='nextPageToken, files(id, name)',
                                              pageToken=page_token).execute()
        for file in response.get('files', []):
            # Process change
            if(file.get('name') == zip_name):
                print ('%s will be deleted' % (file.get('name')))
                deleteFile(file.get('id'))
                # return file.get('id'), file.get('trashed')     
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            return    
    
def deleteFile(file_id):
  """Permanently delete a file, skipping the trash.

  Args:
    file_id: ID of the file to delete.
  """
  try:
    service.files().delete(fileId=file_id).execute()
    # print("Deleted file with ID %s" % file_id)
  except errors.HttpError:
    print ('Check Internet Connection')
 
def downloadFile():
    file_id = getZipId()[0]
    print("Downloading...")
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print ("Downloaded Successfully")     

    with open(zip_absolute_path, "wb") as outfile:
       # Copy the BytesIO stream to the output file
       outfile.write(fh.getbuffer())
       outfile.close()   

    with zipfile.ZipFile(zip_absolute_path, 'r') as zip_ref:
        print("\nUnzipping at " + folder_absolute_path)
        zip_ref.extractall(folder_absolute_path)    
        zip_ref.close()
        os.remove(zip_absolute_path)
        print("Unzipping Done.\n")

if __name__ == '__main__':
        # getZipId()
        # zip_id, trashed = isZipExist()
        # print(zip_id, trashed)
        # downloadFile()
        # folderToZip()        
    try:
        main()
        p = int(input("Press \n 1 for Uploading Backup \n 2 for Downloading Backup \n"))
         
        def uploadFiles():
            uploadFile(os.path.basename(zip_absolute_path), zip_absolute_path, mimeType='application/zip')     
            
        def downloadFiles():
            downloadFile()
         
        switcher = {
                1: uploadFiles,
                2: downloadFiles
            }
         
        def choice(argument):
            func = switcher.get(argument, "nothing")
            return func()
        
        choice(p) 
    except httplib2.ServerNotFoundError:
        print("Check Internet Connection")        
