# mcp_client.py

import asyncio
import sys
import os
from typing import Optional
from contextlib import AsyncExitStack

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

    async def connect_to_server(self, server_script_path: str):
        python_path = sys.executable
        server_params = StdioServerParameters(
            command=python_path,
            args=[server_script_path]
        )
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools
        print("\n✅ Connected to server with tools:", [tool.name for tool in tools])
        return tools

    async def process_query(self, query: str) -> str:
        tools = await self.session.list_tools()
        tool_descriptions = "\n".join([
            f"- {tool.name}: {tool.description}" for tool in tools.tools
        ])

        messages = [{
            "role": "user",
            "content": (
                f"Answer the following query by selecting and chaining tools if necessary.\n\n"
                f"Available tools:\n{tool_descriptions}\n\n"
                f"User query: {query}"
            )
        }]

        system_prompt = (
            "You are a smart autonomous agent. Use the available tools to reason step-by-step through the task. "
            "After using each tool, update your knowledge, then decide if more tools are needed. "
            "Never use tools not related to the task. Do not guess — rely only on tool outputs and logic."
        )

        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in tools.tools]

        final_response = ""
        max_rounds = 8

        for round_num in range(max_rounds):
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1000,
                system=system_prompt,
                messages=messages,
                tools=available_tools
            )

            tool_used = False

            for content in response.content:
                if content.type == "text":
                    messages.append({"role": "assistant", "content": content.text})
                    final_response += f"\n{content.text}"

                elif content.type == "tool_use":
                    tool_used = True
                    tool_name = content.name
                    tool_args = content.input or {}

                    print(f"\n🔧 Calling tool: {tool_name} with args: {tool_args}")
                    result = await self.session.call_tool(tool_name, tool_args)
                    tool_output = result.content[0].text

                    # Inject tool output + re-prompt reasoning step
                    messages.append({
                        "role": "assistant",
                        "content": f"[{tool_name} result]:\n{tool_output}"
                    })
                    messages.append({
                        "role": "user",
                        "content": (
                            f"You just received the result from [{tool_name}]. "
                            f"Think about what this tells you, and if more tools are needed to answer the query: '{query}'."
                        )
                    })

            if not tool_used:
                break

        return final_response.strip()

    async def chat_loop(self):
        print("\n🤖 MCP Client Started")
        print("Type your query or 'quit' to exit.")
        while True:
            try:
                query = input("\n💬 Query: ").strip()
                if query.lower() == 'quit':
                    break
                response = await self.process_query(query)
                print("\n🧠 Response:\n", response)
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        server_path = "./mcp_server.py"
    else:
        server_path = sys.argv[1]

    if sys.platform == 'win32':
        import msvcrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

    client = MCPClient()
    try:
        await client.connect_to_server(server_path)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

