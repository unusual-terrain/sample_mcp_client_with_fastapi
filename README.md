# MCP Client with FastAPI and Claude Integration

This project is a **sample MCP (Modular Control Protocol) client** built using **FastAPI**. It demonstrates how to send user queries to **Anthropic Claude**, handle tool usage via a running **MCP server**, and return AI responses in real-time.

---

## 📦 Project Structure

```
.
├── main.py          # FastAPI app with /query endpoint
├── client.py        # MCPClient class for Claude + MCP interaction
├── .env             # Environment variables (Claude API key, etc.)
├── requirements.txt # Python dependencies
└── README.md        # Project documentation
```

---

## 🔧 Prerequisites

* Python 3.13+
* Claude API key from [Anthropic](https://console.anthropic.com/)
* MCP Server running and exposing a `streamable_http` endpoint

---

## 🚀 Quick Start

1. **Clone this repo**

```bash
git clone git@github.com:unusual-terrain/sample_mcp_client_with_fastapi.git
cd mcp-client
```

2. **Install dependencies**

```bash
uv sync
```

3. **Update `.env` file** with your Claude API key:

```
ANTHROPIC_API_KEY=your_claude_api_key_here
```

4. **Start the FastAPI app**

```bash
make run-dev
```

5. **Test the app**

Visit: [http://localhost:8001/docs](http://localhost:8001/docs)

Or send a POST request:

```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Find candidates who are skilled in Python"}'
```

---

## 🧠 How It Works

### 🔗 MCP Connection

* `client.py` uses `streamablehttp_client` to connect to an MCP server.
* MCP tools are listed dynamically and passed to Claude.

### 💬 Claude Integration

* Claude receives the user query + tool metadata.
* If Claude decides to call a tool, the result is processed via MCP.
* Claude then provides a refined response based on the tool result.

### 🔄 Loopback Architecture

* Tool calls are handled mid-conversation.
* Results are fed back into Claude to allow chained reasoning.

---

## 🧪 Testing

You can test different prompts via the `/query` endpoint.

Example:

```json
{
  "query": "List all job openings for data scientists"
}
```

---

## 🤝 Contributing

PRs and issues are welcome. Make sure your code is typed and follows FastAPI best practices.

---

## 📄 License

MIT

## 🙋 Support

For issues, contact \[[unusual.terrain.9@gmail.com](mailto:unusual.terrain.9@gmail.com)] or raise a GitHub issue.

---

Happy coding! 🎉
