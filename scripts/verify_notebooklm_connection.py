import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def verify_connection():
    command = "npx.cmd" if os.name == 'nt' else "npx"
    server_params = StdioServerParameters(
        command=command,
        args=["-y", "notebooklm-mcp"],
        env={**os.environ, "HEADLESS": "true"}
    )
    
    print("Connecting to NotebookLM MCP server to verify health...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print("Initializing session...")
            await session.initialize()
            
            print("Calling get_health tool...")
            try:
                health = await session.call_tool("get_health", arguments={})
                print(f"Health Status: {health}")
                
                print("\nListing notebooks...")
                notebooks = await session.call_tool("list_notebooks", arguments={})
                print(f"Notebooks: {notebooks}")
                
                print("\nConnection verified successfully!")
            except Exception as e:
                print(f"Verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_connection())
