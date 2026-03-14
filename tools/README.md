# Tools

This directory contains Python scripts that execute deterministic tasks.

## What Goes Here

Each tool is a standalone Python script that:
- Takes clear inputs (command-line args, environment vars, or config files)
- Does one thing reliably
- Returns predictable outputs
- Handles errors gracefully
- Uses API keys from `.env`

## Tool Template

```python
#!/usr/bin/env python3
"""
Tool Name - Brief description

Usage:
    python tool_name.py --input <value>
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main execution function"""
    # Your logic here
    pass

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

## Best Practices

- **One purpose per tool** - Keep scripts focused
- **Use argparse** - For clear command-line interfaces
- **Load from .env** - Never hardcode credentials
- **Validate inputs** - Fail fast with clear error messages
- **Log progress** - Especially for long-running operations
- **Make it testable** - Write functions, not just scripts
- **Document usage** - Include docstring with examples

## Common Patterns

### API Client
```python
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_NAME_KEY')

def call_api(endpoint, data):
    headers = {'Authorization': f'Bearer {API_KEY}'}
    response = requests.post(endpoint, json=data, headers=headers)
    response.raise_for_status()
    return response.json()
```

### File Processing
```python
import json
from pathlib import Path

def process_file(input_path, output_path):
    data = Path(input_path).read_text()
    result = transform(data)
    Path(output_path).write_text(json.dumps(result, indent=2))
```

### Error Handling
```python
import sys

try:
    result = risky_operation()
except RateLimitError as e:
    print(f"Rate limited. Wait {e.retry_after} seconds.", file=sys.stderr)
    sys.exit(2)  # Use exit codes to signal different failure types
except Exception as e:
    print(f"Unexpected error: {e}", file=sys.stderr)
    sys.exit(1)
```
