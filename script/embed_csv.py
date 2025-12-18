#!/usr/bin/env python3
"""Convert CSV file to shell script with curl API call."""

import argparse
import csv
import json
import shlex
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Convert CSV to shell script with curl API call"
    )
    parser.add_argument(
        "store_id",
        help="Store ID to use in the API URL",
    )
    parser.add_argument(
        "csv_file",
        nargs="?",
        default="input/content.csv",
        help="Path to CSV file (default: input/content.csv)",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"Error: File not found: {csv_path}")
        return 1

    results = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

        # Single column - use value only for content
        if len(headers) == 1:
            for row in reader:
                if row:
                    results.append({"content": row[0]})
        else:
            # Two columns: first is content, query is content + ". " + second
            for row in reader:
                if len(row) >= 2:
                    content = row[0]
                    query = f"{row[0]}. {row[1]}"
                    results.append({"content": content, "query": query})

    # Split into batches of 50
    batch_size = 50
    batches = [results[i:i + batch_size] for i in range(0, len(results), batch_size)]

    curl_commands = []
    for batch in batches:
        payload = json.dumps({"items": batch})
        escaped_payload = shlex.quote(payload)
        curl_commands.append(f"""curl -X 'POST' \\
  'http://localhost:8000/v1/stores/{args.store_id}/embed/batch' \\
  -H 'accept: application/json' \\
  -H 'Content-Type: application/json' \\
  -d {escaped_payload}""")

    print("#!/bin/bash")
    print(" && \\\n".join(curl_commands))
    return 0


if __name__ == "__main__":
    exit(main())
