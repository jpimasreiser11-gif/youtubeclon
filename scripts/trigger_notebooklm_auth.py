import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_setup():
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Use npx.cmd on Windows
    command = "npx.cmd" if os.name == 'nt' else "npx"
    
    server_params = StdioServerParameters(
        command=command,
        args=["-y", "notebooklm-mcp"],
        env={**os.environ, "HEADLESS": "false"}
    )
    
    print(f"Connecting to NotebookLM MCP server using {command}...")
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("Initializing session...")
                await session.initialize()
                
                print("Fetching tools list...")
                tools_result = await session.list_tools()
                tool_names = [t.name for t in tools_result.tools]
                print(f"Available tools: {tool_names}")
                
                if "setup_auth" in tool_names:
                    print("\n!!! TRIGGERING AUTHENTICATION !!!")
                    print("A browser window should open shortly. PLEASE LOG IN TO GOOGLE.")
                    print("Wait for the browser to launch and complete the login process.\n")
                    result = await session.call_tool("setup_auth", arguments={})
                    print(f"Result from tool: {result}")
                    print("\nIf the browser opened and you logged in, this script should finish.")
                else:
                    print("Error: setup_auth tool not found in tool list!")
    except FileNotFoundError:
        print(f"Error: {command} not found in PATH.")
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_setup())
