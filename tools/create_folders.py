#!/usr/bin/env python3
"""Create the PDF Conversion System folder structure"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

creds = Credentials.from_authorized_user_file('token.json')
service = build('drive', 'v3', credentials=creds)

try:
    # Create main folder
    main_folder_metadata = {
        'name': 'PDF Conversion System',
        'mimeType': 'application/vnd.google-apps.folder'
    }
    main_folder = service.files().create(
        body=main_folder_metadata,
        fields='id, name'
    ).execute()

    print(f"✓ Created: {main_folder['name']}")
    print(f"  ID: {main_folder['id']}\n")

    # Create subfolders
    subfolders = ['Input', 'Output', 'Processed']
    folder_ids = {}

    for folder_name in subfolders:
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [main_folder['id']]
        }
        folder = service.files().create(
            body=folder_metadata,
            fields='id, name'
        ).execute()

        folder_ids[folder_name.lower()] = folder['id']
        print(f"✓ Created: {folder_name}/")
        print(f"  ID: {folder['id']}")

    print("\n" + "="*80)
    print("✅ Folders created successfully!")
    print("="*80)
    print("\nAdd these to your .env file:")
    print(f"GOOGLE_DRIVE_INPUT_FOLDER_ID={folder_ids['input']}")
    print(f"GOOGLE_DRIVE_OUTPUT_FOLDER_ID={folder_ids['output']}")

    # Try to update .env automatically
    try:
        with open('.env', 'r') as f:
            lines = f.readlines()

        updated_lines = []
        input_updated = False
        output_updated = False

        for line in lines:
            if line.startswith('GOOGLE_DRIVE_INPUT_FOLDER_ID='):
                updated_lines.append(f"GOOGLE_DRIVE_INPUT_FOLDER_ID={folder_ids['input']}\n")
                input_updated = True
            elif line.startswith('GOOGLE_DRIVE_OUTPUT_FOLDER_ID='):
                updated_lines.append(f"GOOGLE_DRIVE_OUTPUT_FOLDER_ID={folder_ids['output']}\n")
                output_updated = True
            else:
                updated_lines.append(line)

        if not input_updated:
            updated_lines.append(f"\nGOOGLE_DRIVE_INPUT_FOLDER_ID={folder_ids['input']}\n")
        if not output_updated:
            updated_lines.append(f"GOOGLE_DRIVE_OUTPUT_FOLDER_ID={folder_ids['output']}\n")

        with open('.env', 'w') as f:
            f.writelines(updated_lines)

        print("\n✓ Updated .env file!")

    except Exception as e:
        print(f"\n⚠ Could not auto-update .env: {e}")
        print("Please update manually with the IDs above.")

except HttpError as error:
    print(f"❌ Error creating folders: {error}")

