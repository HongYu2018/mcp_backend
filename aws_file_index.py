import boto3
from openai import OpenAI
import json
import tiktoken
from io import BytesIO
from botocore.exceptions import NoCredentialsError, ClientError
from pdfminer.high_level import extract_text
import os
import sys
from dotenv import load_dotenv

# 🧱 Safe console encoding for Windows
#sys.stdout = sys.__stdout__ = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

tokenizer = tiktoken.encoding_for_model("gpt-4o")
MAX_TOKENS = 8000
SUPPORTED_EXTENSIONS = ('.txt', '.md', '.csv', '.log', '.pdf')
INDEX_FILE = "s3_file_index.json"

def num_tokens(text):
    return len(tokenizer.encode(text))

def chunk_text(text, max_tokens=MAX_TOKENS):
    words = text.split()
    chunks, chunk, tokens = [], [], 0

    for word in words:
        word_tokens = num_tokens(word + ' ')
        if tokens + word_tokens > max_tokens:
            chunks.append(' '.join(chunk))
            chunk = [word]
            tokens = word_tokens
        else:
            chunk.append(word)
            tokens += word_tokens

    if chunk:
        chunks.append(' '.join(chunk))
    return chunks

def analyze_chunk_with_gpt(text_chunk):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant that indexes files by extracting title, topics, keywords and summary."},
                {"role": "user", "content": f"Extract title, main topics, keywords and a detailed summary from the following:\n\n{text_chunk}"}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[OpenAI API error] {e}")
        return None

def load_existing_index():
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_index(index):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

def index_s3_text_files(bucket_name, aws_access_key, aws_secret_key, region_name, prefix):
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region_name
    )

    existing_index = load_existing_index()
    updated_index = {}

    paginator = s3.get_paginator('list_objects_v2')
    operation_parameters = {'Bucket': bucket_name, 'Prefix': prefix}

    for page in paginator.paginate(**operation_parameters):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if not key.lower().endswith(SUPPORTED_EXTENSIONS):
                print(f"[Skipped] Unsupported file: {key}")
                continue

            try:
                response = s3.get_object(Bucket=bucket_name, Key=key)
                raw_data = response['Body'].read()

                if key.lower().endswith('.pdf'):
                    content = extract_text(BytesIO(raw_data))
                else:
                    content = raw_data.decode('utf-8', errors='ignore')

                if not content.strip():
                    print(f"[Skipped] Empty or unreadable: {key}")
                    continue

                chunks = chunk_text(content)
                chunk_count = len(chunks)

                if key in existing_index and existing_index[key].get("chunks") == chunk_count:
                    print(f"[Cached] Skipping already indexed file: {key}")
                    continue

                print(f"[Processing] {key} ({chunk_count} chunks)")
                summaries = []
                for i, chunk in enumerate(chunks):
                    print(f" - Chunk {i+1}/{chunk_count}")
                    summary = analyze_chunk_with_gpt(chunk)
                    summaries.append(summary or "[Error] GPT returned nothing")

                updated_index[key] = {
                    "chunks": chunk_count,
                    "summaries": summaries
                }

            except (NoCredentialsError, ClientError) as e:
                print(f"[AWS Error] {key}: {e}")
            except Exception as e:
                print(f"[Error] {key}: {e}")

    if updated_index:
        existing_index.update(updated_index)
        save_index(existing_index)
        print(f"[Done] Indexed {len(updated_index)} new document(s)")
    else:
        print("[Info] No new documents indexed.")

    return existing_index
