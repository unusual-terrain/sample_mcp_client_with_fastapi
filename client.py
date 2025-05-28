from contextlib import AsyncExitStack
import traceback
from dotenv import load_dotenv

from anthropic import Anthropic, APIStatusError
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Default MCP server URL (replace with your actual MCP server endpoint)
MCP_CLIENT_URL = "http://0.0.0.0:8000/recruit/mcp"

# Load environment variables from .env file (if used for ANTHROPIC_API_KEY update .env with your api key.)
load_dotenv()


class MCPClient:
    """
    A sample MCP Client that connects to a running MCP server,
    sends user queries to Claude, and handles tool_use calls via MCP.
    """

    def __init__(self, server_url: str = MCP_CLIENT_URL):
        self.server_url = server_url
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()  # Claude API client

    async def test_connection(self):
        """
        Checks if the MCP server is reachable and tools can be listed.
        Used at app startup for health checks.
        """
        try:
            async with streamablehttp_client(self.server_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    await session.list_tools()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to MCP server: {e}")

    async def process_query(self, query: str) -> str:
        """
        Handles a user query by sending it to Claude with tool metadata,
        processes any tool_use request by Claude via MCP, and returns the final response.
        """
        try:
            async with streamablehttp_client(self.server_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    # Step 1: Retrieve list of available tools from the MCP server
                    try:
                        tool_response = await session.list_tools()
                        available_tools = [
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "input_schema": tool.inputSchema,
                            }
                            for tool in tool_response.tools
                        ]
                    except APIStatusError as e:
                        raise RuntimeError(
                            f"Claude API error: {e.status_code} - {e.response}"
                        )

                    # Step 2: Prepare initial Claude message
                    messages = [{"role": "user", "content": query}]
                    assistant_content = []
                    final_text = []

                    # Step 3: Call Claude with tools provided
                    response = self.anthropic.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1000,
                        system="You are a helpful AI assistant. The output should be human readable",
                        messages=messages,
                        tools=available_tools,
                    )

                    # Step 4: Parse Claude's response
                    for content in response.content:
                        if content.type == "text":
                            # Normal text response
                            final_text.append(content.text)
                            assistant_content.append(content)

                        elif content.type == "tool_use":
                            # Claude requested a tool call
                            tool_name = content.name
                            tool_args = content.input
                            tool_id = content.id

                            try:
                                # Step 5: Call the requested MCP tool
                                tool_result = await session.call_tool(tool_name, tool_args)

                                # Log tool call success and prepare context for follow-up
                                final_text.append(
                                    f"[Tool `{tool_name}` called with args {tool_args}]"
                                )
                                assistant_content.append(content)
                                messages.extend([
                                    {
                                        "role": "assistant",
                                        "content": assistant_content,
                                    },
                                    {
                                        "role": "user",
                                        "content": [
                                            {
                                                "type": "tool_result",
                                                "tool_use_id": tool_id,
                                                "content": tool_result.content,
                                            }
                                        ],
                                    },
                                ])

                                # Step 6: Ask Claude for a follow-up message after tool result
                                response = self.anthropic.messages.create(
                                    model="claude-3-5-sonnet-20241022",
                                    max_tokens=1000,
                                    messages=messages,
                                    tools=available_tools,
                                )

                                for followup in response.content:
                                    if followup.type == "text":
                                        final_text.append(followup.text)

                            except Exception as e:
                                # If tool call fails, append an error message to the response
                                print(f"Tool call failed: {e}")
                                final_text.append(
                                    f"Error calling tool `{tool_name}`: {e}"
                                )

            # Return the combined final response as a string
            return "\n".join(final_text)

        except* Exception as eg:
            # Handle any grouped exceptions (PEP 654)
            print(f"Unhandled ExceptionGroup:\n{eg}")
            for ex in eg.exceptions:
                print(f"  - {type(ex).__name__}: {ex}")
                traceback.print_exception(type(ex), ex, ex.__traceback__)
            raise RuntimeError(f"Error processing query via MCP: {eg}")

    async def cleanup(self) -> None:
        """
        Clean up async resources (e.g. open contexts).
        Call this during shutdown if needed.
        """
        try:
            await self.exit_stack.aclose()
            print("[MCPClient] Cleanup successful.")
        except Exception as e:
            print(f"[MCPClient] Cleanup error: {e}")
