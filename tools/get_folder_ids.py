#!/usr/bin/env python3
"""Quick script to get folder IDs from Google Drive"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Use existing token
creds = Credentials.from_authorized_user_file('token.json')
service = build('drive', 'v3', credentials=creds)

# Search for PDF Conversion System folder
query = "name='PDF Conversion System' and mimeType='application/vnd.google-apps.folder' and trashed=false"
results = service.files().list(q=query, fields='files(id, name)').execute()
main_folders = results.get('files', [])

if not main_folders:
    print("❌ 'PDF Conversion System' folder not found!")
    print("The folder creation may have failed.")
else:
    main_folder = main_folders[0]
    print(f"✓ Found: {main_folder['name']}")
    print(f"  ID: {main_folder['id']}\n")

    # Get subfolders
    query = f"'{main_folder['id']}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields='files(id, name)').execute()
    subfolders = results.get('files', [])

    folder_ids = {}
    for folder in subfolders:
        print(f"✓ Found: {folder['name']}/")
        print(f"  ID: {folder['id']}")

        if folder['name'] == 'Input':
            folder_ids['input'] = folder['id']
        elif folder['name'] == 'Output':
            folder_ids['output'] = folder['id']

    if folder_ids:
        print("\n" + "="*80)
        print("Add these to your .env file:")
        print("="*80)
        print(f"GOOGLE_DRIVE_INPUT_FOLDER_ID={folder_ids.get('input', 'NOT_FOUND')}")
        print(f"GOOGLE_DRIVE_OUTPUT_FOLDER_ID={folder_ids.get('output', 'NOT_FOUND')}")
