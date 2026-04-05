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
    Provide a prioritized list of technical steps to implement:
    1. Virality Scoring Heuristic
    2. Dynamic Subtitle Styles (Hormozi style)
    3. Smart Reframing with Split Screen
    4. B-Roll Generation
    
    Match these to our codebase (FastAPI backend in 'scripts' and Next.js frontend in 'app').
    """
    
    output_file = r"docs\notebooklm_advice.txt"
    
    print("Consulting NotebookLM...")
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("ask_question", arguments={"question": query})
                
                with open(output_file, "w", encoding="utf-8") as f:
                    # Accessing the text content from the ToolResult
                    text_content = ""
                    for content in result.content:
                        if hasattr(content, 'text'):
                            text_content += content.text
                    f.write(text_content)
                print(f"Advice saved to {output_file}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(query_notebook())
