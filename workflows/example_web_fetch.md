# Example: Fetch and Process Web Data

## Objective
Demonstrate the WAT framework by fetching data from a URL and extracting specific information.

## Required Inputs
- `url`: The target URL to fetch
- `output_file`: Where to save the processed results (optional)

## Tools Used
- `fetch_url.py` - Fetches content from a URL and saves it to `.tmp/`
- `process_data.py` - Processes the fetched content (to be created as needed)

## Process
1. Validate the URL format
2. Run `fetch_url.py` to download the content
3. Check if fetch was successful
4. Process or analyze the content as needed
5. Save results to specified location or cloud service

## Expected Outputs
- Raw data saved to `.tmp/fetched_data.json`
- Processed results to Google Sheets or specified output

## Edge Cases
- **Invalid URL**: Validate before attempting fetch
- **Network timeout**: Retry with exponential backoff
- **Rate limits**: Respect retry-after headers
- **Large files**: Stream instead of loading into memory

## Learnings
(This section gets updated as we encounter issues and discover solutions)
