import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def query_notebook():
    command = "npx.cmd" if os.name == 'nt' else "npx"
    server_params = StdioServerParameters(
        command=command,
        args=["-y", "notebooklm-mcp"],
        env={**os.environ, "HEADLESS": "true"}
    )
    
    query = """
    Based on the 'OpusClips Clone Improvements Guide', provide a prioritized list of technical steps 
    to implement the following in our current codebase:
    1. Virality Scoring Heuristic
    2. Dynamic Subtitle Styles (Hormozi style)
    3. Smart Reframing with Split Screen
    4. B-Roll Generation
    
    Be specific about which files to modify if possible.
    """
    
    print("Consulting NotebookLM for implementation details...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Use ask_question. It automatically targets the active notebook.
            result = await session.call_tool("ask_question", arguments={
                "question": query
            })
            print(f"Advice from NotebookLM:\n{result}")

if __name__ == "__main__":
    asyncio.run(query_notebook())
