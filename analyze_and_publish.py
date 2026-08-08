import sys
import os
from datetime import datetime, timezone, timedelta
from xai_sdk import Client
from xai_sdk.chat import system, user, file

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_and_publish.py <path_to_json>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Exiting cleanly.")
        sys.exit(0)

    # Initialize native xAI client (uses XAI_API_KEY environment variable)
    client = Client()

    print(f"Uploading {file_path} to xAI Files API...")
    uploaded_file = client.files.upload(file_path)
    file_id = uploaded_file.id
    print(f"File uploaded successfully. Assigned File ID: {file_id}")

    utc_now = datetime.now(timezone.utc)
    edt_now = utc_now - timedelta(hours=4)
    last_updated_str = edt_now.strftime("%B %d, %Y at %I:%M %p EDT")

    system_prompt_text = """
You are a community manager analyzing a Discord chat log for Age of Mythology: Retold. 
Review the attached chat log in JSON format and produce a markdown-formatted report.

REQUIREMENTS:
1. Extract the key insights regarding game balance.
2. Credit player names organically within the insights.
3. Create a list of recommended balance changes.
4. Format the output with specific headings: `### Insights into Game Balance` and `### Recommended Balance Changes`.
"""

    try:
        print("Sending chat request with attached file_id to xAI API...")

        chat = client.chat.create(
            model="grok-4.5",
            messages=[system(system_prompt_text)]
        )
        
        # Attach the uploaded file using the file() helper inside user()
        chat.append(user(
            "Analyze the attached raw Discord chat export JSON file.",
            file(file_id)
        ))
        
        response = chat.sample()
        llm_output = response.content

    finally:
        # Clean up remote file storage after completion
        print(f"Cleaning up remote file {file_id} from xAI storage...")
        try:
            client.files.delete(file_id)
        except Exception as e:
            print(f"Warning: Failed to delete remote file {file_id}: {e}")

    final_document = f"""---
layout: page
title: "Latest Balance Report"
permalink: /
---

**Last Updated:** {last_updated_str}

---

{llm_output}
"""
    
    out_filename = "index.md"
    with open(out_filename, "w", encoding="utf-8") as f:
        f.write(final_document)

    print(f"Successfully updated {out_filename}")

if __name__ == "__main__":
    main()