#!/usr/bin/env python3
"""
Google Drive Setup - Authenticate and configure Google Drive API access

Usage:
    python tools/setup_google_drive.py

This script will:
1. Guide you through Google Cloud Project setup
2. Authenticate with Google Drive API using OAuth
3. Generate token.json for future API calls
4. Help you get your folder IDs for the .env file
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Google API libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Error: Google API libraries not installed.", file=sys.stderr)
    print("Run: pip install google-auth google-auth-oauthlib google-api-python-client", file=sys.stderr)
    sys.exit(1)

# If modifying these scopes, delete the file token.json
SCOPES = ['https://www.googleapis.com/auth/drive']


def get_credentials():
    """
    Authenticate with Google Drive API and return credentials.
    Creates token.json after successful authentication.
    """
    creds = None
    token_path = 'token.json'
    credentials_path = 'credentials.json'

    # Check if credentials.json exists
    if not Path(credentials_path).exists():
        print("\n❌ Error: credentials.json not found!")
        print("\nTo set up Google Drive API access:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Create a new project (or select existing)")
        print("3. Enable the Google Drive API:")
        print("   - Go to 'APIs & Services' > 'Enable APIs and Services'")
        print("   - Search for 'Google Drive API' and enable it")
        print("4. Create OAuth 2.0 credentials:")
        print("   - Go to 'APIs & Services' > 'Credentials'")
        print("   - Click 'Create Credentials' > 'OAuth client ID'")
        print("   - Choose 'Desktop app' as application type")
        print("   - Download the JSON file and save it as 'credentials.json' in this directory")
        print("\nOnce you have credentials.json, run this script again.")
        sys.exit(1)

    # Token.json stores the user's access and refresh tokens
    if Path(token_path).exists():
        print("Found existing token.json")
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("\n🔐 Starting OAuth authentication flow...")
            print("Your browser will open for Google authentication.")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print(f"✓ Credentials saved to {token_path}")

    return creds


def list_folders(service, max_results=20):
    """
    List folders in Google Drive to help user find folder IDs.
    """
    try:
        print("\n📁 Listing your Google Drive folders:\n")

        # Search for folders only
        query = "mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query,
            pageSize=max_results,
            fields="files(id, name, parents)",
            orderBy="name"
        ).execute()

        items = results.get('files', [])

        if not items:
            print("No folders found.")
            return

        print(f"{'Folder Name':<40} {'Folder ID'}")
        print("-" * 80)
        for item in items:
            print(f"{item['name']:<40} {item['id']}")

        print(f"\nShowing {len(items)} folders (max {max_results})")

    except HttpError as error:
        print(f"An error occurred: {error}", file=sys.stderr)


def create_folder_structure(service):
    """
    Optionally create the folder structure for PDF conversion workflow.
    """
    print("\n📂 Would you like to create the folder structure for this workflow?")
    print("   This will create:")
    print("   - PDF Conversion System/")
    print("     - Input/")
    print("     - Output/")
    print("     - Processed/")

    response = input("\nCreate folders? (y/n): ").lower().strip()

    if response != 'y':
        print("Skipping folder creation.")
        return None

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

        print(f"\n✓ Created: {main_folder['name']} (ID: {main_folder['id']})")

        # Create subfolders
        subfolders = ['Input', 'Output', 'Processed']
        folder_ids = {'main': main_folder['id']}

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
            print(f"✓ Created: {folder_name}/ (ID: {folder['id']})")

        return folder_ids

    except HttpError as error:
        print(f"An error occurred: {error}", file=sys.stderr)
        return None


def update_env_file(folder_ids):
    """
    Update .env file with folder IDs.
    """
    env_path = Path('.env')

    if not env_path.exists():
        print("\n❌ Error: .env file not found!")
        return

    # Read current .env content
    with open(env_path, 'r') as f:
        lines = f.readlines()

    # Update folder ID lines
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

    # If lines don't exist, add them
    if not input_updated:
        updated_lines.append(f"GOOGLE_DRIVE_INPUT_FOLDER_ID={folder_ids['input']}\n")
    if not output_updated:
        updated_lines.append(f"GOOGLE_DRIVE_OUTPUT_FOLDER_ID={folder_ids['output']}\n")

    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)

    print(f"\n✓ Updated .env file with folder IDs")
    print(f"   Input folder ID:  {folder_ids['input']}")
    print(f"   Output folder ID: {folder_ids['output']}")


def main():
    print("=" * 80)
    print("Google Drive Setup for PDF to Word Conversion Workflow")
    print("=" * 80)

    # Authenticate and get credentials
    creds = get_credentials()

    print("\n✓ Successfully authenticated with Google Drive!")

    # Build the service
    try:
        service = build('drive', 'v3', credentials=creds)
        print("✓ Google Drive API service created")
    except HttpError as error:
        print(f"An error occurred: {error}", file=sys.stderr)
        sys.exit(1)

    # List existing folders
    list_folders(service)

    # Option to create folder structure
    folder_ids = create_folder_structure(service)

    if folder_ids:
        # Update .env file with new folder IDs
        update_env_file(folder_ids)
    else:
        print("\n📋 Manual Setup Instructions:")
        print("   1. Note the folder IDs from the list above")
        print("   2. Update your .env file with:")
        print("      GOOGLE_DRIVE_INPUT_FOLDER_ID=<your_input_folder_id>")
        print("      GOOGLE_DRIVE_OUTPUT_FOLDER_ID=<your_output_folder_id>")

    print("\n" + "=" * 80)
    print("✓ Setup complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Ensure your .env file has the correct folder IDs")
    print("2. Test the conversion tool: python tools/pdf_to_word.py --input test.pdf --output test.docx")
    print("3. Run the polling script: python tools/poll_drive_folder.py")
    print("\nFor help, see workflows/pdf_to_word_conversion.md")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
