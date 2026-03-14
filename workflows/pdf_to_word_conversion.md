# PDF to Word Conversion Workflow

## Objective
Automatically convert PDFs to formatted Word documents following strict publication formatting specifications. PDFs uploaded to a Google Drive input folder are processed, converted, and saved to an output folder with source PDFs archived in a processed subfolder.

## Required Inputs
- **PDF file**: Uploaded to the designated Google Drive input folder
- **Google Drive folders**: Three folders set up (Input, Output, Processed)
- **Credentials**: OAuth credentials for Google Drive API access

## Tools Used
- `setup_google_drive.py` - One-time authentication and folder setup
- `pdf_to_word.py` - Core PDF to Word conversion with formatting rules
- `poll_drive_folder.py` - Monitors Google Drive folder and orchestrates conversion

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- PyMuPDF4LLM and PyMuPDF for PDF processing
- python-docx for Word document generation
- Google API libraries for Drive integration
- EasyOCR for scanned document support

### 2. Google Cloud Project Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the Google Drive API:
   - Navigate to "APIs & Services" > "Enable APIs and Services"
   - Search for "Google Drive API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the JSON file
   - Save it as `credentials.json` in the project root directory

### 3. Run Setup Script

```bash
python tools/setup_google_drive.py
```

This will:
- Authenticate with Google Drive (opens browser)
- Generate `token.json` for future API calls
- Optionally create the folder structure
- List your folders to help you identify folder IDs
- Update your `.env` file with folder IDs

### 4. Configure Environment Variables

Your `.env` file should contain:
```
GOOGLE_DRIVE_INPUT_FOLDER_ID=<your_input_folder_id>
GOOGLE_DRIVE_OUTPUT_FOLDER_ID=<your_output_folder_id>
GOOGLE_DRIVE_PROCESSED_FOLDER_ID=<your_processed_folder_id>
ANTHROPIC_API_KEY=<your_anthropic_api_key>
```

**API Keys:**
- `ANTHROPIC_API_KEY`: Required for AI-powered image description and classification
  - Get your key from: https://console.anthropic.com
  - Used to identify whether images are figures or tables
  - Generates descriptive names for each extracted image

## Process Flow

### Automatic Workflow (Polling)

```
1. Upload PDF → Input folder (Google Drive)
2. poll_drive_folder.py detects new file
3. Downloads PDF to .tmp/
4. Runs pdf_to_word.py for conversion:
   - Extracts and cleans text
   - Extracts all images to .tmp/images/
   - Uses Claude AI to describe each image
   - Generates descriptive filenames
   - Creates formatted Word document
5. Uploads Word document → Output folder
6. Uploads extracted images → Processed/ folder
7. Moves PDF → Processed/ folder
8. Cleans up temporary files
9. Logs file ID to prevent reprocessing
```

### Manual Conversion

You can also convert PDFs manually without Google Drive:

```bash
python tools/pdf_to_word.py --input document.pdf --output formatted.docx
```

For scanned PDFs requiring OCR:
```bash
python tools/pdf_to_word.py --input scanned.pdf --output formatted.docx --ocr
```

## Formatting Specifications

### 1. Filename Cleaning

**Rule**: Remove leading numbers, trim to 50 characters, remove cut-off words

**Good example**:
```
texas-adapted-genetic-strategies-for-beef-cattle.pdf
```

**Bad example** (automatically fixed):
```
058-texas-adapted-genetic-strategies-for-beef-cattle-v.pdf
```

### 2. Author Handling

- Copy author names under the title
- Remove position titles (Professor, Ph.D., etc.)
- Remove superscripts, stars, symbols from author names
- Separate with commas
- Keep superscripts in main text for citations

### 3. Text Cleanup

**All-caps headings**: Convert to title case
```
FEEDING STRATEGIES → Feeding Strategies
```

**Extra line breaks**: Remove triple+ newlines
```
Line 1\n\n\nLine 2 → Line 1\n\nLine 2
```

**Double spacing**: Replace with single space

**Non-circular bullets**: Replace with standard bullets (•)
- Arrows (→, ►, ➔) → •
- Squares (■, □) → •
- Diamonds (◆, ◇) → •

**Long dashes at bullets**: Remove em-dashes attached to words
```
—Word → Word
```

**Fractional numbers**: Format correctly
```
1-1/8 → 1 1/8
1/8inches → 1/8 inches
```

### 4. Heading Detection

The tool automatically detects heading hierarchy:
- **H1**: Document title (with [H1] comment)
- **H2**: Major sections (with [H2] comment)
- **H3**: Subsections (with [H3] comment)
- **H4**: Sub-subsections (with [H4] comment)

Each heading has a visible comment in brackets indicating its level for easy manual review.

### 5. Text Formatting

**All body text uses consistent formatting:**
- **Font**: Calibri
- **Size**: 11pt
- **Color**: Black (default)

This ensures the document has a professional, uniform appearance throughout. Only heading styles differ from this baseline formatting.

### 6. Lists

- Bullet points are converted to Word's built-in List Bullet style
- Nesting levels are preserved where detected
- List text also uses consistent Calibri 11pt formatting

### 7. Image Extraction and Processing

**Automatic Image Extraction:**
- All images are automatically extracted from the PDF
- Each image is analyzed using Claude's vision AI
- Images are classified as either **Figure** (photos, drawings, charts, graphs) or **Table** (data in rows/columns)
- Images are given descriptive names based on their content

**Naming Convention:**
- Format: `NNN Type N Description`
- **NNN** = Overall order in PDF (001, 002, 003...) - sequential for ALL images
- **Type** = Either "Figure" or "Table"
- **N** = Type-specific counter (separate counters for Figures and Tables)
- **Description** = AI-generated description of content

**Example Sequence:**
- 1st image (table) → `001 Table 1 Production Data.png`
- 2nd image (figure) → `002 Figure 1 Cow Farm.png`
- 3rd image (figure) → `003 Figure 2 Grazing Cattle.png`
- 4th image (table) → `004 Table 2 Cost Analysis.png`

Note: Figure and Table counters are independent. The first figure is always "Figure 1" regardless of when it appears.

**Storage:**
- Extracted images are uploaded to the Google Drive **Processed** folder
- Images are saved alongside the source PDF for easy reference
- Local temporary copies are automatically cleaned up after upload

**Word Document References:**
- The Word document includes a list of all extracted images with their filenames
- Each image entry shows the page number where it appeared in the source PDF
- Images are ready to be inserted manually into the document as needed

## Running the Workflow

### Option 1: Continuous Monitoring (Recommended for Active Use)

```bash
python tools/poll_drive_folder.py
```

This runs continuously, checking the folder every 5 minutes (default). Press Ctrl+C to stop.

### Option 2: Single Run (Good for Testing)

```bash
python tools/poll_drive_folder.py --once
```

Processes any new PDFs once and exits.

### Option 3: Custom Interval

```bash
python tools/poll_drive_folder.py --interval 600
```

Check every 10 minutes (600 seconds).

### Option 4: Scheduled with Cron (Mac/Linux)

Add to crontab to run every 5 minutes:
```bash
*/5 * * * * cd /path/to/project && python tools/poll_drive_folder.py --once
```

### Option 5: Task Scheduler (Windows)

Create a scheduled task to run `poll_drive_folder.py --once` every 5 minutes.

## Expected Outputs

### Successful Conversion

**Input**: `058-texas-beef-cattle-strategies-2024-draft.pdf` (Google Drive Input folder)

**Outputs**:
1. `texas-beef-cattle-strategies.docx` (Google Drive Output folder)
   - Cleaned filename
   - Authors listed under title
   - Formatted headings with [H1], [H2], etc. comments
   - Clean text with proper spacing (Calibri 11pt)
   - Standardized bullets
   - List of extracted images with filenames

2. Extracted images (Google Drive Processed/ folder)
   - `001 Table 1 Production Data.png` (first image, first table)
   - `002 Figure 1 Cattle in Feedlot.png` (second image, first figure)
   - `003 Figure 2 Grazing System.png` (third image, second figure)
   - `004 Table 2 Cost Analysis.png` (fourth image, second table)
   - (etc. - one file per image found in PDF)

3. Source PDF moved to Processed/ folder

4. Log entry in `.tmp/processed_files.json` to prevent reprocessing

### File Locations

- **Temporary files**: `.tmp/` (local, auto-cleaned)
- **Temporary images**: `.tmp/images/` (local, auto-cleaned after upload)
- **Processed log**: `.tmp/processed_files.json` (local)
- **Final Word docs**: Google Drive Output folder
- **Extracted images**: Google Drive Processed/ folder
- **Archived PDFs**: Google Drive Processed/ folder

## Edge Cases

### OCR Failure on Badly Scanned PDFs

**Symptom**: No text extracted or garbled text

**Solutions**:
1. Ensure PDF quality is sufficient (300+ DPI for scans)
2. Use `--ocr` flag explicitly: `python tools/pdf_to_word.py --input file.pdf --output file.docx --ocr`
3. Pre-process with OCRmyPDF: `ocrmypdf input.pdf output.pdf`
4. If still failing, manual conversion may be required

**Prevention**: Scan documents at high resolution before uploading

### Google Drive API Rate Limits

**Limit**: 750 queries per 100 seconds per user

**Symptom**: HTTP 429 errors

**Solutions**:
1. Reduce polling frequency (increase --interval)
2. Process files in smaller batches
3. Wait 100 seconds before retrying
4. Tool automatically retries after errors

**Prevention**: Don't poll more frequently than every 2 minutes if processing many files

### Invalid PDF Format

**Symptom**: "Error extracting PDF content" message

**Solutions**:
1. Verify PDF is not corrupted (open in Adobe Reader)
2. Re-save PDF from source application
3. Use PDF repair tool
4. Check file actually is a PDF (some files have wrong extension)

**Prevention**: Validate PDFs before uploading

### Missing or Incomplete Content

**Symptom**: Word document missing sections or images

**Solutions**:
1. Check source PDF for actual content
2. For scanned documents, use OCR mode
3. For complex layouts, may require manual review
4. Images always need manual insertion

**Expected behavior**: Tool notes missing images with placeholders

### Webhook Timeout/Failures

**Note**: Currently using polling, not webhooks. This edge case applies only if upgraded to webhook-based monitoring.

**Symptom**: Files uploaded but not processed

**Solutions**:
1. Check webhook server is running
2. Verify webhook URL is publicly accessible (HTTPS)
3. Check Google Drive notifications are configured
4. Fall back to polling mode

### Authentication Expiration

**Symptom**: "Credentials expired" error

**Solution**:
```bash
python tools/setup_google_drive.py
```

This refreshes the authentication token.

**Prevention**: Token should auto-refresh, but run setup again if issues persist

## Learnings

This section will be updated as we encounter real-world issues and discover better approaches.

### Initial Implementation Notes

- **PyMuPDF4LLM vs pdfplumber**: PyMuPDF4LLM chosen for better heading detection and structure preservation
- **Polling vs Webhooks**: Polling chosen for simplicity and local execution without server requirements
- **OCR Strategy**: Digital text extraction first, fallback to OCR only when needed (saves processing time)
- **Filename cleaning**: Regex approach handles most cases, but manual review recommended for edge cases

### Known Limitations

1. **Image Insertion**: Images are noted but not automatically inserted due to licensing and positioning complexity
2. **Heading Detection**: Relies on font size heuristics; very unusual formatting may require manual adjustment
3. **Table Handling**: Basic table support; complex tables may need manual formatting
4. **Author Extraction**: Pattern-based; uncommon author formats may require manual correction

### Future Enhancements

- [ ] Add automatic image insertion with proper positioning
- [ ] Improve table detection and formatting
- [ ] Add confidence scoring for OCR results
- [ ] Implement webhook support for real-time processing
- [ ] Add email notifications for completed conversions
- [ ] Create dashboard for monitoring processing status

## Troubleshooting

### "credentials.json not found"
→ Run Google Cloud setup (see Setup Instructions above)

### "token.json not found"
→ Run `python tools/setup_google_drive.py`

### "Folder IDs not configured"
→ Check `.env` file has `GOOGLE_DRIVE_INPUT_FOLDER_ID` and `GOOGLE_DRIVE_OUTPUT_FOLDER_ID`

### "PyMuPDF libraries not installed"
→ Run `pip install -r requirements.txt`

### Conversion produces incorrect formatting
→ Test with sample PDFs and iterate on formatting rules in `pdf_to_word.py`
→ Some PDFs may require manual post-processing

### No files being processed
1. Check PDFs are in Input folder (not Processed subfolder)
2. Verify `.tmp/processed_files.json` - file IDs may already be logged
3. Delete the log file to reprocess: `rm .tmp/processed_files.json`
4. Check polling script is running: `ps aux | grep poll_drive_folder`

## Support

For issues or enhancements:
1. Check this workflow document for solutions
2. Review tool output for specific error messages
3. Test conversion locally first: `python tools/pdf_to_word.py --input test.pdf --output test.docx`
4. Check `.tmp/` logs for detailed error information

## Version History

- **v1.0** (2026-02-07): Initial implementation with polling-based monitoring
  - Core PDF to Word conversion
  - Google Drive integration
  - Filename cleaning and text formatting rules
  - Author extraction
  - Heading detection
  - Image placeholders
