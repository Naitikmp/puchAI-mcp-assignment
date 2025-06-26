# 📱 PuchAI MCP Server

This is a [FastMCP](https://github.com/Naitikmp/puchAI-mcp-assignment)-based server built to work with **PuchAI**, a WhatsApp-first AI assistant designed for Indian users. The backend exposes smart tools like weather, resume sharing, web search, and more through a machine-consumable control protocol (MCP).

---

## 🚀 Features

- 📝 `resume`: Serve your resume as raw Markdown.
- 📱 `validate`: Return your registered WhatsApp number.
- 🌐 `fetch`: Simplify any webpage and serve its text content.
- 🌦️ `weather`: Get real-time weather from Open-Meteo (no API key needed).
- 🔍 `search`: Fetch search results using DuckDuckGo.
- 📅 `calendar` _(Coming Soon)_: Google Calendar integration.

---

## 🧱 Tech Stack

- Python 3.10+
- `fastmcp` for server + tool registration
- `mcp` for core protocol support
- Flask (for upcoming OAuth/Google auth callback)
- Async/Await structure
- Tools modularized under `tools/`

---

## 🔧 Installation

```bash
git clone https://github.com/Naitikmp/puchAI-mcp-assignment
cd puchai-mcp
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
