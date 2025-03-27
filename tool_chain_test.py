import asyncio
import sys
import os
from datetime import datetime
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("bucket_name_l")
AWS_KEY = os.getenv("aws_access_key_l")
AWS_SECRET = os.getenv("aws_secret_key_l")
AWS_REGION = os.getenv("region_name_l")
PREFIX = os.getenv("prefix_l")

# Import your tool implementations
from report import generate_sales_analysis_report as gsar
from data_display import display_database as dd
from aws_s3_read import get_s3_structure_string
from aws_file_index import index_s3_text_files as indexs
from generate_response import generate_reasoning_and_graph as reasoning

files = get_s3_structure_string(
    bucket_name=BUCKET_NAME,
    aws_access_key=AWS_KEY,
    aws_secret_key=AWS_SECRET,
    region_name=AWS_REGION,
    prefix=PREFIX)
            
print([types.TextContent(type="text", text=f"🗂 Incident Files:\n{files}")])

indexing_result = indexs(
    bucket_name=BUCKET_NAME,
    aws_access_key=AWS_KEY,
    aws_secret_key=AWS_SECRET,
    region_name=AWS_REGION,
    prefix=PREFIX)
                
print([types.TextContent(type="text", text="✅ S3 files indexed successfully.")])

#query = arguments.get("query", "No query provided.")
print('Enter your query:')
query=input()
summary, graph = reasoning(query)
print('reasoning start ...')
print([types.TextContent(type="text", text=f"🧠 Reasoning Summary:\n{summary}"), types.TextContent(type="text", text=f"🗺 Note Graph JSON:\n{graph}")])