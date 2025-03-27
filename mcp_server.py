# mcp_server.py
import asyncio
from datetime import datetime
import sys
import os
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from report import generate_sales_analysis_report as gsar
from data_display import display_database as dd
from aws_s3_read import get_s3_structure_string
from aws_file_index import index_s3_text_files as indexs
from generate_response import generate_reasoning_and_graph as reasoning

from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("bucket_name_l")
AWS_KEY = os.getenv("aws_access_key_l")
AWS_SECRET = os.getenv("aws_secret_key_l")
AWS_REGION = os.getenv("region_name_l")
PREFIX = os.getenv("prefix_l")

# Create server instance
server = Server("mcp-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="get-datetime",
            description="Get the current date and time",
            inputSchema={
                "type": "object",
                "properties": {},  # No input needed
                "required": []
            }
        ),
        types.Tool(
            name="get-salereport",
            description="Generate a sales analysis report from the database.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        types.Tool(
            name="get-database_data",
            description="Display all available data from internal system database.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        types.Tool(
            name="get-incident_files",
            description="List aircraft incident PDF files from S3.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        types.Tool(
            name="get-aws_s3_file_indexing",
            description="Index the S3 incident files for chunk-level keyword and topic extraction.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        types.Tool(
            name="get-reasoning_output",
            description="Generate a reasoning summary and note-graph based on a query over indexed S3 content for aircraft incident.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution"""
    if name == "get-datetime":
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [
            types.TextContent(
                type="text",
                text=f"Current date and time: {current_time}"
            )
        ]
    if name == "get-salereport":
        report = gsar()
        return [types.TextContent(type="text", text=f"📊 Sales Report:\n{report}")]

    if name == "get-database_data":
        data = dd()
        return [types.TextContent(type="text", text=f"📚 Database Data:\n{data}")]
    
    if name == "get-incident_files":
        #print('Connecting to AWS S3...')
        files = get_s3_structure_string(
            bucket_name=BUCKET_NAME,
            aws_access_key=AWS_KEY,
            aws_secret_key=AWS_SECRET,
            region_name=AWS_REGION,
            prefix=PREFIX
        )
        return [types.TextContent(type="text", text=f"🗂 Incident Files:\n{files}")]

    if name == "get-aws_s3_file_indexing":
        #print('Check indexing or create indexing...')
        indexing_result = indexs(
            bucket_name=BUCKET_NAME,
            aws_access_key=AWS_KEY,
            aws_secret_key=AWS_SECRET,
            region_name=AWS_REGION,
            prefix=PREFIX
        )
        return [types.TextContent(type="text", text="✅ S3 files indexed successfully.")]    

    if name == "get-reasoning_output":
        query = arguments.get("query", "No query provided.")
        #print('Reasoning start!...')
        summary, graph = reasoning(query)
        summary = reasoning(query)
        return [
            types.TextContent(type="text", text=f"🧠 Reasoning Summary:\n{summary[0:3000]}...")
            #types.TextContent(type="text", text=f"🗺 Note Graph JSON:\n{graph}")
        ]    

    raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the server"""
    # Set binary mode for stdin/stdout on Windows
    if sys.platform == 'win32':
        import msvcrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            )
        )

if __name__ == "__main__":
    asyncio.run(main())