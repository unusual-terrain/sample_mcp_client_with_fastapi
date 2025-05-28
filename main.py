from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pydantic import BaseModel

from client import MCPClient  # Import your custom MCPClient to interact with MCP server

# Initialize the MCP client instance
mcp_client = MCPClient()


# Lifespan handler to test MCP server connection during startup
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    This function runs when the FastAPI app starts and shuts down.
    It ensures the MCP server is reachable before continuing.
    """
    try:
        print("🔌 Testing MCP server connection on startup...")
        await mcp_client.test_connection()  # Ping MCP server
        print("✅ MCP server is reachable.")
        yield
    except Exception as e:
        print(f"❌ MCP server connection failed: {e}")
        raise RuntimeError(f"MCP connection failed: {e}")


# Initialize FastAPI app with lifespan management
app = FastAPI(
    lifespan=lifespan,
    title="Sample MCP Client with FastAPI",
    version="1.0.0",
    description="This is a sample MCP Client using FastAPI. It connects to an MCP server and sends user queries to it.",
)


# Request body model for /query endpoint
class QueryRequest(BaseModel):
    query: str  # User query to be processed by MCP server


# Health check route to confirm the client server is running
@app.get("/")
async def app_status_check():
    """
    A simple health check endpoint to verify the client is up.
    """
    return {
        "name": "SAMPLE_MCP_CLIENT_WITH_FASTAPI",
        "description": "MCP client that processes user queries by communicating with an MCP server.",
        "version": "1.0",
        "status": "Running Ok!",
    }


# POST endpoint to handle user queries and forward them to the MCP server
@app.post("/query")
async def handle_query(request: QueryRequest):
    """
    Accepts a user query, forwards it to the MCP server,
    and returns the response back to the caller.

    Expected body: { "query": "your question or command here" }
    """
    try:
        print(f"📥 Received query: {request.query}")

        # Forward the query to MCP and await the response
        response = await mcp_client.process_query(request.query)
        print(f"📤 Response from MCP: {response}")

        return {"response": response}
    
    except RuntimeError as e:
        # Raised when MCP client fails internally
        print(f"Runtime error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        # For any other unexpected errors
        print(f"Unexpected error: {e}")
        return JSONResponse(status_code=400, content={"detail": str(e)})
