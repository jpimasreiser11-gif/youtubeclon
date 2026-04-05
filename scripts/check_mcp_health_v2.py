import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def check_health():
    command = "npx.cmd" if os.name == 'nt' else "npx"
    server_params = StdioServerParameters(
        command=command,
        args=["-y", "notebooklm-mcp"],
        env={**os.environ, "HEADLESS": "true"}
    )
    
    output_file = r"docs\mcp_health.txt"
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_health", arguments={})
            
            with open(output_file, "w", encoding="utf-8") as f:
                text_content = ""
                for content in result.content:
                    if hasattr(content, 'text'):
                        text_content += content.text
                f.write(text_content)
            print(f"Health saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(check_health())
