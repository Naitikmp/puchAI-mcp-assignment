# 📱 PuchAI MCP Server

This is a [FastMCP](https://github.com/Naitikmp/puchAI-mcp-assignment)-based server built to work with **PuchAI**, a WhatsApp-first AI assistant designed for Indian users. The backend exposes smart tools like weather, resume sharing, web search, and more through a machine-consumable control protocol (MCP).

---

## 🚀 Features

- 📝 `resume`: Serve your resume as raw Markdown.
- 📱 `validate`: Return your registered WhatsApp number.
- 🌐 `fetch`: Simplify any webpage and serve its text content.
- 🌦️ `weather`: Get real-time weather from Open-Meteo (no API key needed).
- 🔍 `search`: Fetch search results using DuckDuckGo.
- 📅 `calendar`: Google Calendar integration (connect, add events, list events, schedule meetings).
- 🗺️ `map`: Geocode, reverse geocode, directions, distance, nearby places, elevation, and more.
- ✈️ `flight`: Flight status, airport info, search flights, travel info.
- 🚚 `parcel`: Track parcels from major Indian couriers, auto-detect courier, list supported couriers.
- 🚗 `vehicle`: Check vehicle challans and RC (registration) info.
- 🚆 `train`: Live train status, trains between stations, PNR status, train schedule, station live status.
- 💹 `stock`: Get stock prices, compare stocks, get market news.
- 🎨 `ascii_art`: Generate ASCII art with styles, decorations, and message types.

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

```

---

## 🛠️ Tool Overview

### Core Tools
- **resume**: Serve your resume as Markdown.
- **validate**: Return your registered WhatsApp number.
- **fetch**: Fetch and simplify webpage content.

### Extra Tools
- **weather**: Get current weather for a city.
- **search**: Web search using DuckDuckGo.

### Calendar Tools
- **connect_calendar**: Connect your Google Calendar (OAuth).
- **add_event_for_user**: Add an event to your calendar.
- **list_upcoming_events**: List your next 5 events.
- **schedule_google_meet**: Schedule a Google Meet meeting.

### Map Tools
- **search_location**: Geocode an address or place name.
- **reverse_geocode_coordinates**: Get address from coordinates.
- **calculate_distance_between_locations**: Distance between two locations.
- **get_directions_between_locations**: Directions from A to B.
- **find_nearby_places**: Find places (e.g., restaurants) near a location.
- **get_location_elevation**: Get elevation for a location.

### Flight Tools
- **get_flight_status**: Get status for a flight.
- **get_airport_info**: Get info for an airport.
- **search_flights**: Search flights between airports.
- **get_travel_info**: General travel info.

### Parcel Tracker Tools
- **track_parcel**: Track a parcel by number and courier.
- **detect_courier_service**: Auto-detect courier from tracking number.
- **list_supported_couriers**: List all supported couriers.

### Vehicle Tools
- **check_challan**: Check pending challans (traffic fines) for a vehicle.
- **check_vehicle_rc**: Fetch vehicle registration (RC) details.

### Train Tools
- **get_live_train_status**: Live status for a train.
- **get_trains_between_stations**: List trains between two stations.
- **get_pnr_status_tool**: Check PNR status.
- **get_train_schedule_tool**: Get train schedule.
- **get_station_live_status**: Live status for a station.

### Stock Market Tools
- **get_stock_price**: Get current stock price for a symbol.
- **compare_stock_prices**: Compare up to 5 stocks.
- **get_market_news**: Get latest market news.

### ASCII Art Tools
- **generate_ascii_art**: Generate ASCII art with styles, decorations, and message types.

---

## 📖 Usage

All tools are exposed as MCP endpoints and can be called via the FastMCP server. Example usage (Python):

```python
from fastmcp import FastMCP
mcp = FastMCP("My MCP Server", token="YOUR_TOKEN")
result = await mcp.call_tool("weather", city="Mumbai")
print(result)
```

For WhatsApp or other integrations, see the [PuchAI frontend](https://github.com/Naitikmp/puchAI-mcp-assignment) or your client code.

### Example Tool Calls
- **Weather**: `weather(city="Delhi")`
- **Stock Price**: `get_stock_price(stock_symbol="RELIANCE.NS")`
- **Train Status**: `get_live_train_status(train_number="12345", date="2024-06-28")`
- **ASCII Art**: `generate_ascii_art(text="Hello", style="big", decoration="fire")`
- **Flight Status**: `get_flight_status(flight_number="AI101")`
- **Parcel Tracking**: `track_parcel(tracking_number="AB123456789IN")`
- **Google Calendar**: `add_event_for_user(user_id, title, start_time, end_time)`

---

## ⚙️ Configuration

Some tools require API keys. Set these as environment variables or in a `.env` file:

- `TOKEN` (required): Your MCP server token
- `MY_NUMBER`: Your WhatsApp number (for validate tool)
- `RESUME_FILE`: Path to your resume file (default: `resume.md`)
- `FMP_API_KEY`: [Financial Modeling Prep](https://financialmodelingprep.com/) API key (stock prices)
- `STOCK_NEWS_API_KEY`: [NewsAPI](https://newsapi.org/) key (market news)
- `ATTESTER_API_KEY`: [Attestr](https://attestr.com/) API key (vehicle RC info)
- `OPENCAGE_API_KEY`: [OpenCage](https://opencagedata.com/) API key (geocoding)
- `GOOGLE_MAPS_API_KEY`: [Google Maps](https://console.cloud.google.com/) API key (geocoding, maps)

For Google Calendar integration, follow the OAuth setup instructions in the code and set up your credentials as described in the `tools/calender_tools.py` docstrings.

---

## 📂 Directory Structure

- `main.py` — Server entrypoint, registers all tools
- `tools/` — All tool modules (see above)
- `config.py` — Configuration and API keys
- `utils/` — Utility code (e.g., authentication)
- `states/`, `tokens/` — User and token state (for calendar, etc.)

---

## 📝 License

MIT
