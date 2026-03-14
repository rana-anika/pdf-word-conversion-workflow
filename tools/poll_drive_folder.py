#!/usr/bin/env python3
"""
Poll Google Drive Folder - Monitor folder for new PDFs and convert them

Usage:
    python tools/poll_drive_folder.py [--interval 300] [--once]

Options:
    --interval: Polling interval in seconds (default: 300 = 5 minutes)
    --once: Run once and exit (for manual/cron execution)

This script:
1. Polls the input Google Drive folder for new PDF files
2. Downloads each new PDF
3. Converts it to Word using pdf_to_word.py
4. Uploads the Word document to the output folder
5. Moves the PDF to the processed subfolder
"""

import os
import sys
import time
import argparse
import subprocess
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Google API libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
except ImportError:
    print("Error: Google API libraries not installed.", file=sys.stderr)
    print("Run: pip install google-auth google-auth-oauthlib google-api-python-client", file=sys.stderr)
    sys.exit(1)

# Configuration
INPUT_FOLDER_ID = os.getenv('GOOGLE_DRIVE_INPUT_FOLDER_ID')
OUTPUT_FOLDER_ID = os.getenv('GOOGLE_DRIVE_OUTPUT_FOLDER_ID')
PROCESSED_FOLDER_ID = os.getenv('GOOGLE_DRIVE_PROCESSED_FOLDER_ID')
SCOPES = ['https://www.googleapis.com/auth/drive']

# Track processed files
PROCESSED_FILES_LOG = '.tmp/processed_files.json'


def load_processed_files():
    """Load the list of already processed file IDs."""
    if Path(PROCESSED_FILES_LOG).exists():
        with open(PROCESSED_FILES_LOG, 'r') as f:
            return json.load(f)
    return []


def save_processed_files(processed_files):
    """Save the list of processed file IDs."""
    Path(PROCESSED_FILES_LOG).parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_FILES_LOG, 'w') as f:
        json.dump(processed_files, f, indent=2)


def get_credentials():
    """Get Google Drive API credentials from token.json."""
    creds = None
    token_path = 'token.json'

    if not Path(token_path).exists():
        print("❌ Error: token.json not found!", file=sys.stderr)
        print("Run: python tools/setup_google_drive.py first to authenticate", file=sys.stderr)
        sys.exit(1)

    creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        else:
            print("❌ Error: Credentials expired. Run setup_google_drive.py again.", file=sys.stderr)
            sys.exit(1)

    return creds


def list_new_pdfs(service, folder_id, processed_files):
    """
    List new PDF files in the folder that haven't been processed yet.
    """
    try:
        query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(
            q=query,
            fields='files(id, name, modifiedTime)',
            orderBy='modifiedTime desc'
        ).execute()

        items = results.get('files', [])

        # Filter out already processed files
        new_files = [f for f in items if f['id'] not in processed_files]

        return new_files

    except HttpError as error:
        print(f"Error listing files: {error}", file=sys.stderr)
        return []


def download_file(service, file_id, destination):
    """Download a file from Google Drive."""
    try:
        request = service.files().get_media(fileId=file_id)

        Path(destination).parent.mkdir(parents=True, exist_ok=True)

        with open(destination, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"  Download progress: {progress}%", end='\r')

        print(f"\n  ✓ Downloaded to: {destination}")
        return True

    except HttpError as error:
        print(f"  Error downloading file: {error}", file=sys.stderr)
        return False


def upload_file(service, file_path, folder_id, file_name=None):
    """Upload a file to Google Drive."""
    try:
        if file_name is None:
            file_name = Path(file_path).name

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }

        media = MediaFileUpload(file_path, resumable=True)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()

        print(f"  ✓ Uploaded to Google Drive: {file['name']}")
        print(f"    View at: {file['webViewLink']}")
        return file['id']

    except HttpError as error:
        print(f"  Error uploading file: {error}", file=sys.stderr)
        return None


def move_file(service, file_id, new_parent_id, old_parent_id):
    """Move a file to a different folder."""
    try:
        # Retrieve the existing parents to remove
        file = service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents'))

        # Move the file to the new folder
        file = service.files().update(
            fileId=file_id,
            addParents=new_parent_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()

        print(f"  ✓ Moved to Processed folder")
        return True

    except HttpError as error:
        print(f"  Error moving file: {error}", file=sys.stderr)
        return False


def convert_pdf_to_word(pdf_path, word_path):
    """
    Call the pdf_to_word.py tool to convert PDF to Word.
    Returns tuple: (success: bool, images_dir: Path or None)
    """
    try:
        cmd = [
            sys.executable,
            'tools/pdf_to_word.py',
            '--input', pdf_path,
            '--output', word_path,
            '--extract-images'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"  ✓ Conversion successful")
            # Check if images were extracted
            images_dir = Path('.tmp/images')
            if images_dir.exists() and any(images_dir.iterdir()):
                return True, images_dir
            return True, None
        else:
            print(f"  ❌ Conversion failed:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return False, None

    except Exception as e:
        print(f"  Error running conversion: {e}", file=sys.stderr)
        return False, None


def upload_images_to_drive(service, images_dir, processed_folder_id):
    """
    Upload all extracted images to Google Drive Processed folder.
    Returns number of images uploaded.
    """
    if not images_dir or not images_dir.exists():
        return 0

    uploaded_count = 0
    image_files = list(images_dir.glob('*'))

    if not image_files:
        return 0

    print(f"  Uploading {len(image_files)} images to Processed folder...")

    for image_path in image_files:
        try:
            file_metadata = {
                'name': image_path.name,
                'parents': [processed_folder_id]
            }

            media = MediaFileUpload(str(image_path), resumable=True)

            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()

            print(f"    ✓ Uploaded: {image_path.name}")
            uploaded_count += 1

        except Exception as e:
            print(f"    ✗ Failed to upload {image_path.name}: {e}", file=sys.stderr)
            continue

    return uploaded_count


def process_file(service, file_info, processed_folder_id, output_folder_id):
    """
    Process a single PDF file:
    1. Download
    2. Convert to Word (with image extraction)
    3. Upload Word doc
    4. Upload extracted images
    5. Move PDF to processed folder
    """
    file_id = file_info['id']
    file_name = file_info['name']

    print(f"\n{'='*80}")
    print(f"Processing: {file_name}")
    print(f"{'='*80}")

    # Create temp paths
    temp_pdf = Path('.tmp') / file_name
    temp_word = temp_pdf.with_suffix('.docx')

    try:
        # Step 1: Download PDF
        print("1. Downloading PDF...")
        if not download_file(service, file_id, str(temp_pdf)):
            return False

        # Step 2: Convert to Word (with image extraction)
        print("2. Converting to Word and extracting images...")
        success, images_dir = convert_pdf_to_word(str(temp_pdf), str(temp_word))
        if not success:
            return False

        # Step 3: Upload Word document
        print("3. Uploading Word document...")
        if not upload_file(service, str(temp_word), output_folder_id):
            return False

        # Step 4: Upload extracted images (if any)
        if images_dir:
            print("4. Uploading extracted images...")
            uploaded_count = upload_images_to_drive(service, images_dir, processed_folder_id)
            print(f"  ✓ Uploaded {uploaded_count} images to Processed folder")
        else:
            print("4. No images to upload")

        # Step 5: Move PDF to processed folder
        print("5. Moving PDF to Processed folder...")
        if not move_file(service, file_id, processed_folder_id, INPUT_FOLDER_ID):
            return False

        # Cleanup temp files
        temp_pdf.unlink(missing_ok=True)
        temp_word.unlink(missing_ok=True)

        # Cleanup extracted images
        if images_dir and images_dir.exists():
            import shutil
            shutil.rmtree(images_dir, ignore_errors=True)
            print("  ✓ Cleaned up temporary image files")

        print(f"\n✓ Successfully processed: {file_name}")
        return True

    except Exception as e:
        print(f"Error processing file: {e}", file=sys.stderr)
        return False


def poll_folder(service, once=False):
    """
    Main polling loop.
    """
    if not INPUT_FOLDER_ID or not OUTPUT_FOLDER_ID or not PROCESSED_FOLDER_ID:
        print("❌ Error: Folder IDs not configured in .env file!", file=sys.stderr)
        print("Run: python tools/setup_google_drive.py", file=sys.stderr)
        sys.exit(1)

    # Use Processed folder from environment
    processed_folder_id = PROCESSED_FOLDER_ID

    # Load processed files log
    processed_files = load_processed_files()

    print(f"\n{'='*80}")
    print(f"Monitoring Input folder for new PDFs")
    print(f"Input folder ID:  {INPUT_FOLDER_ID}")
    print(f"Output folder ID: {OUTPUT_FOLDER_ID}")
    print(f"Already processed: {len(processed_files)} files")
    print(f"{'='*80}\n")

    while True:
        try:
            # Check for new PDFs
            new_pdfs = list_new_pdfs(service, INPUT_FOLDER_ID, processed_files)

            if new_pdfs:
                print(f"\n🔔 Found {len(new_pdfs)} new PDF(s) to process\n")

                for pdf_file in new_pdfs:
                    # Process the file
                    success = process_file(service, pdf_file, processed_folder_id, OUTPUT_FOLDER_ID)

                    if success:
                        # Add to processed list
                        processed_files.append(pdf_file['id'])
                        save_processed_files(processed_files)
                    else:
                        print(f"❌ Failed to process: {pdf_file['name']}", file=sys.stderr)

            else:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] No new files. Waiting...", end='\r')

            # Exit if running once
            if once:
                print("\n\n✓ Polling complete (--once mode)")
                break

            # Wait before next poll
            time.sleep(args.interval if 'args' in globals() else 300)

        except KeyboardInterrupt:
            print("\n\n⚠ Polling stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error in polling loop: {e}", file=sys.stderr)
            if once:
                break
            print("Retrying in 60 seconds...")
            time.sleep(60)


def main():
    global args
    parser = argparse.ArgumentParser(description='Monitor Google Drive folder for new PDFs to convert')
    parser.add_argument('--interval', type=int, default=300, help='Polling interval in seconds (default: 300)')
    parser.add_argument('--once', action='store_true', help='Run once and exit (for cron)')

    args = parser.parse_args()

    print("=" * 80)
    print("PDF to Word - Google Drive Folder Monitor")
    print("=" * 80)

    # Get credentials
    creds = get_credentials()

    # Build service
    try:
        service = build('drive', 'v3', credentials=creds)
    except HttpError as error:
        print(f"An error occurred: {error}", file=sys.stderr)
        sys.exit(1)

    # Start polling
    poll_folder(service, once=args.once)


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
