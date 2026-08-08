import sys
import json
import os
from datetime import datetime, timezone, timedelta
from openai import OpenAI

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_and_publish.py <path_to_json>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Exiting cleanly.")
        sys.exit(0)

    client = OpenAI(
        base_url="https://api.x.ai/v1",
        api_key=os.environ.get("XAI_API_KEY"),
    )

    # Upload the JSON file to the xAI files API
    with open(file_path, "rb") as file_data:
        uploaded_file = client.files.create(
            file=file_data,
            purpose="agents"  # Required for agentic file tool calling
        )

    # Convert the runner's UTC time to EDT for the display stamp
    utc_now = datetime.now(timezone.utc)
    edt_now = utc_now - timedelta(hours=4)
    last_updated_str = edt_now.strftime("%B %d, %Y at %I:%M %p EDT")

    # The dynamic frontmatter is removed from the system prompt 
    # to ensure Grok focuses strictly on the data analysis
    system_prompt = f"""
You are a community manager analyzing a Discord chat log for Age of Mythology: Retold. 
Review the uploaded chat log in JSON format and produce a markdown-formatted report.

REQUIREMENTS:
1. Extract the key insights regarding game balance.
2. Credit player names organically within the insights.
3. Create a list of recommended balance changes.
4. Format the output with specific headings: `### Insights into Game Balance` and `### Recommended Balance Changes`.
"""

    print("Sending data to Grok API...")
    
    response = client.chat.completions.create(
        model="grok-4.5",
        messages=[
            {"role": "system", "content": system_prompt}
        ],
        file_ids=[uploaded_file.id],
        temperature=0.2
    )

    llm_output = response.choices[0].message.content

    # Construct the final markdown document programmatically
    final_document = f"""---
layout: page
title: "Latest Balance Report"
permalink: /
---

**Last Updated:** {last_updated_str}

---

{llm_output}
"""
    
    # Overwrite the root index.md file
    out_filename = "index.md"
    with open(out_filename, "w", encoding="utf-8") as f:
        f.write(final_document)

    print(f"Successfully updated {out_filename}")

if __name__ == "__main__":
    main()