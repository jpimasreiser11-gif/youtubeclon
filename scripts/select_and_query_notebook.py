import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def select_and_query():
    command = "npx.cmd" if os.name == 'nt' else "npx"
    server_params = StdioServerParameters(
        command=command,
        args=["-y", "notebooklm-mcp"],
        env={**os.environ, "HEADLESS": "true"}
    )
    
    notebook_id = "opusclips-clone-improvements-g"
    query = "Provide the prioritized implementation steps for the OpusClips improvements as discussed in the documentation provided in this notebook."
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print(f"Selecting notebook {notebook_id}...")
            select_result = await session.call_tool("select_notebook", arguments={"id": notebook_id})
            print(f"Select Result: {select_result}")
            
            print("Checking health again...")
            health = await session.call_tool("get_health", arguments={})
            print(f"Health: {health}")
            
            print("Querying NotebookLM...")
            result = await session.call_tool("ask_question", arguments={"question": query})
            print(f"Advice: {result}")

if __name__ == "__main__":
    asyncio.run(select_and_query())
