
import json
import requests
from mcp import ErrorData, McpError
from mcp.types import TextContent
from duckduckgo_search import DDGS
from openai import BaseModel

def register_extra_tools(mcp):
    class RichToolDescription(BaseModel):
        description: str
        use_when: str
        side_effects: str | None

    WeatherToolDesc = RichToolDescription(
        description="Get current weather for a city.",
        use_when="user asks for weather",
        side_effects="Calls Open-Meteo and Nominatim APIs"
    )

    @mcp.tool(description=WeatherToolDesc.model_dump_json())
    async def weather(city: str) -> str:
        city = city.strip()
        if not city:
            raise McpError(ErrorData(code=1, message="City name is required"))
        try:
            geo_url = f"https://nominatim.openstreetmap.org/search?format=json&limit=1&q={city}"
            geo_resp = requests.get(geo_url, headers={"User-Agent": "MCPWeatherTool/1.0"})
            data = geo_resp.json()
            if not data:
                return f"City '{city}' not found."
            lat, lon = data[0]["lat"], data[0]["lon"]
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=Asia/Kolkata"
            wdata = requests.get(weather_url).json()
            current = wdata.get("current_weather")
            if not current:
                return "Could not get weather info."
            return f"**Weather in {city.title()}**: {current['temperature']}°C, Wind {current['windspeed']} km/h."
        except Exception as e:
            return f"<error>Weather lookup failed: {e}</error>"

    SearchToolDesc = RichToolDescription(
        description="Search the web using DuckDuckGo.",
        use_when="user asks for external info",
        side_effects="Returns top web links"
    )

    @mcp.tool(description=SearchToolDesc.model_dump_json())
    async def web_search(query: str) -> list[TextContent]:
        q = query.strip()
        if not q:
            raise McpError(ErrorData(code=1, message="Empty search query"))
        results = DDGS().text(q, max_results=5)
        if not results:
            return [TextContent(type="text", text="*(No results found)*")]
        output = [f"- **{r.get('title', 'Untitled')}** – {r.get('href', '')}" for r in results]
        return [TextContent(type="text", text="\n".join(output))]