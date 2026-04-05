import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def create_improvements_notebook():
    command = "npx.cmd" if os.name == 'nt' else "npx"
    server_params = StdioServerParameters(
        command=command,
        args=["-y", "notebooklm-mcp"],
        env={**os.environ, "HEADLESS": "true"}
    )
    
    source_path = r"docs\research_improvements.md"
    
    print("Connecting to NotebookLM MCP server...")
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # List tools to get the correct calling sequence
                tools_result = await session.list_tools()
                print(f"Available tools: {[t.name for t in tools_result.tools]}")
                
                # We'll use 'add_notebook' or similar. 
                # Let's try to find if there's a tool to add content.
                # Usually, 'add_notebook' creates a notebook and adds the first source.
                
                print("Creating the notebook and adding the research document...")
                # Assuming 'add_notebook' takes a title or the content itself.
                # Based on the documentation for notebooklm-mcp, it usually takes a URL or local file content.
                
                with open(source_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Most notebooklm MCP servers have an 'add_notebook' that takes 'title' and 'content' or 'file_path'
                # Let's try to be generic or check the tool definition.
                
                # I'll call 'add_notebook' with the title and content.
                result = await session.call_tool("add_notebook", arguments={
                    "name": "OpusClips Clone Improvements Guide",
                    "content": content
                })
                print(f"Result: {result}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_improvements_notebook())
