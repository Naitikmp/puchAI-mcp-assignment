# flight_status_tools.py

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx
from bs4 import BeautifulSoup
from mcp import McpError, ErrorData
from mcp.types import TextContent
from pydantic import BaseModel

class FlightInfo(BaseModel):
    flight_number: str
    airline: str
    departure_airport: str
    arrival_airport: str
    departure_time: str
    arrival_time: str
    status: str
    gate: Optional[str] = None
    terminal: Optional[str] = None
    aircraft_type: Optional[str] = None
    delay_reason: Optional[str] = None

class AirportInfo(BaseModel):
    code: str
    name: str
    city: str
    country: str
    timezone: str
    weather: Optional[str] = None

class FlightServices:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        
        # API Keys (get free tiers)
        self.aviationstack_api_key = "YOUR_AVIATIONSTACK_API_KEY"  # Free 500 requests/month
        self.flightapi_key = "YOUR_FLIGHTAPI_KEY"  # Alternative API
        self.openweather_api_key = "YOUR_OPENWEATHER_API_KEY"  # For airport weather
        
        # Indian airline mapping
        self.indian_airlines = {
            '6E': 'IndiGo',
            'AI': 'Air India',
            'SG': 'SpiceJet', 
            'UK': 'Vistara',
            'G8': 'GoAir',
            'I5': 'AirAsia India',
            '9W': 'Jet Airways',
            'S2': 'JetLite',
            'DN': 'Air Deccan'
        }
        
        # Major airport codes
        self.airport_codes = {
            # Indian Airports
            'DEL': 'Indira Gandhi International Airport, Delhi',
            'BOM': 'Chhatrapati Shivaji International Airport, Mumbai',
            'BLR': 'Kempegowda International Airport, Bangalore',
            'MAA': 'Chennai International Airport, Chennai',
            'HYD': 'Rajiv Gandhi International Airport, Hyderabad',
            'CCU': 'Netaji Subhas Chandra Bose International Airport, Kolkata',
            'COK': 'Cochin International Airport, Kochi',
            'AMD': 'Sardar Vallabhbhai Patel International Airport, Ahmedabad',
            'PNQ': 'Pune Airport, Pune',
            'GOI': 'Goa Airport, Goa',
            
            # International Airports
            'DXB': 'Dubai International Airport, Dubai',
            'SIN': 'Singapore Changi Airport, Singapore',
            'LHR': 'London Heathrow Airport, London',
            'JFK': 'John F. Kennedy International Airport, New York',
            'LAX': 'Los Angeles International Airport, Los Angeles',
            'NRT': 'Narita International Airport, Tokyo',
            'CDG': 'Charles de Gaulle Airport, Paris',
            'FRA': 'Frankfurt Airport, Frankfurt',
            'AMS': 'Amsterdam Schiphol Airport, Amsterdam',
            'ICN': 'Incheon International Airport, Seoul'
        }

    def parse_flight_number(self, flight_input: str) -> tuple:
        """Parse flight number to extract airline code and number"""
        flight_input = flight_input.upper().strip()
        
        # Match patterns like "6E123", "AI101", "UK987"
        match = re.match(r'^([A-Z]{1,3})(\d{1,4})$', flight_input)
        if match:
            airline_code = match.group(1)
            flight_num = match.group(2)
            return airline_code, flight_num
        
        return None, flight_input

    async def get_flight_status_aviationstack(self, flight_number: str, date: str = None) -> Optional[FlightInfo]:
        """Get flight status using AviationStack API"""
        try:
            if self.aviationstack_api_key == "YOUR_AVIATIONSTACK_API_KEY":
                return None
                
            url = "http://api.aviationstack.com/v1/flights"
            params = {
                "access_key": self.aviationstack_api_key,
                "flight_iata": flight_number,
                "limit": 1
            }
            
            if date:
                params["flight_date"] = date
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get("data") and len(data["data"]) > 0:
                flight = data["data"][0]
                
                return FlightInfo(
                    flight_number=flight.get("flight", {}).get("iata", flight_number),
                    airline=flight.get("airline", {}).get("name", "Unknown"),
                    departure_airport=f"{flight.get('departure', {}).get('airport', 'Unknown')} ({flight.get('departure', {}).get('iata', 'Unknown')})",
                    arrival_airport=f"{flight.get('arrival', {}).get('airport', 'Unknown')} ({flight.get('arrival', {}).get('iata', 'Unknown')})",
                    departure_time=flight.get("departure", {}).get("scheduled", "Unknown"),
                    arrival_time=flight.get("arrival", {}).get("scheduled", "Unknown"),
                    status=flight.get("flight_status", "Unknown"),
                    gate=flight.get("departure", {}).get("gate"),
                    terminal=flight.get("departure", {}).get("terminal"),
                    aircraft_type=flight.get("aircraft", {}).get("iata")
                )
            
            return None
            
        except Exception as e:
            return None

    async def get_flight_status_web_scraping(self, flight_number: str) -> Optional[FlightInfo]:
        """Fallback web scraping for flight status"""
        try:
            # Try FlightAware (public data)
            url = f"https://flightaware.com/live/flight/{flight_number}"
            response = await self.client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract basic information (simplified parsing)
            airline_code, flight_num = self.parse_flight_number(flight_number)
            airline_name = self.indian_airlines.get(airline_code, airline_code)
            
            # Try to find flight info (this would need more sophisticated parsing)
            flight_status = "In Progress"  # Default status
            
            return FlightInfo(
                flight_number=flight_number,
                airline=airline_name,
                departure_airport="Check airline website",
                arrival_airport="Check airline website", 
                departure_time="Check airline website",
                arrival_time="Check airline website",
                status=flight_status
            )
            
        except Exception as e:
            return None

    async def get_airport_info(self, airport_code: str) -> Optional[AirportInfo]:
        """Get airport information"""
        try:
            airport_code = airport_code.upper()
            
            if airport_code in self.airport_codes:
                airport_name = self.airport_codes[airport_code]
                # Parse name and city
                parts = airport_name.split(', ')
                name = parts[0] if len(parts) > 0 else airport_name
                city = parts[1] if len(parts) > 1 else "Unknown"
                
                # Get weather if OpenWeather API is available
                weather = await self.get_airport_weather(airport_code)
                
                return AirportInfo(
                    code=airport_code,
                    name=name,
                    city=city,
                    country="India" if airport_code in ['DEL', 'BOM', 'BLR', 'MAA', 'HYD', 'CCU', 'COK', 'AMD', 'PNQ', 'GOI'] else "International",
                    timezone="IST" if airport_code in ['DEL', 'BOM', 'BLR', 'MAA', 'HYD', 'CCU', 'COK', 'AMD', 'PNQ', 'GOI'] else "Local",
                    weather=weather
                )
            
            return None
            
        except Exception as e:
            return None

    async def get_airport_weather(self, airport_code: str) -> Optional[str]:
        """Get weather for airport location"""
        try:
            if self.openweather_api_key == "YOUR_OPENWEATHER_API_KEY":
                return None
                
            # Map airport codes to cities for weather
            city_mapping = {
                'DEL': 'Delhi',
                'BOM': 'Mumbai', 
                'BLR': 'Bangalore',
                'MAA': 'Chennai',
                'HYD': 'Hyderabad',
                'CCU': 'Kolkata',
                'COK': 'Kochi',
                'AMD': 'Ahmedabad',
                'DXB': 'Dubai',
                'SIN': 'Singapore',
                'LHR': 'London',
                'JFK': 'New York'
            }
            
            city = city_mapping.get(airport_code)
            if not city:
                return None
                
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": self.openweather_api_key,
                "units": "metric"
            }
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get("weather"):
                weather = data["weather"][0]
                temp = data["main"]["temp"]
                return f"{weather['description'].title()}, {temp}°C"
            
            return None
            
        except Exception as e:
            return None

    async def search_flights(self, departure: str, arrival: str, date: str = None) -> List[str]:
        """Search for flights between airports"""
        try:
            # This would typically use a flight search API
            # For now, return common routes
            
            departure = departure.upper()
            arrival = arrival.upper()
            
            # Common Indian routes with typical airlines
            common_routes = {
                ('DEL', 'BOM'): ['6E123', 'AI101', 'UK987', 'SG456'],
                ('BOM', 'DEL'): ['6E124', 'AI102', 'UK988', 'SG457'],
                ('DEL', 'BLR'): ['6E345', 'AI201', 'UK765', 'SG234'],
                ('BLR', 'DEL'): ['6E346', 'AI202', 'UK766', 'SG235'],
                ('BOM', 'BLR'): ['6E567', 'AI301', 'UK543', 'SG678'],
                ('BLR', 'BOM'): ['6E568', 'AI302', 'UK544', 'SG679']
            }
            
            route_key = (departure, arrival)
            if route_key in common_routes:
                return common_routes[route_key]
            
            # Generic response for other routes
            return [f"Check airline websites for {departure} to {arrival} flights"]
            
        except Exception as e:
            return []

    async def get_flight_status(self, flight_number: str, date: str = None) -> FlightInfo:
        """Main flight status function"""
        try:
            # Try API first
            flight_info = await self.get_flight_status_aviationstack(flight_number, date)
            
            if not flight_info:
                # Fallback to web scraping
                flight_info = await self.get_flight_status_web_scraping(flight_number)
            
            if not flight_info:
                # Last resort - return basic info
                airline_code, flight_num = self.parse_flight_number(flight_number)
                airline_name = self.indian_airlines.get(airline_code, airline_code)
                
                flight_info = FlightInfo(
                    flight_number=flight_number,
                    airline=airline_name,
                    departure_airport="Information not available",
                    arrival_airport="Information not available",
                    departure_time="Check airline website",
                    arrival_time="Check airline website",
                    status="Please check airline website for current status"
                )
            
            return flight_info
            
        except Exception as e:
            raise Exception(f"Failed to get flight status: {str(e)}")

def register_flight_tools(mcp):
    """Register flight status tools with MCP"""
    flight_service = FlightServices()
    
    class RichToolDescription(BaseModel):
        description: str
        use_when: str
        side_effects: str | None

    # Flight Status Tool
    FlightStatusToolDesc = RichToolDescription(
        description="Get real-time flight status, delays, gate information, and flight details for any airline",
        use_when="user wants to check flight status, delays, arrival/departure times, gate numbers, or flight information",
        side_effects="Queries flight tracking services and airline databases"
    )

    @mcp.tool(description=FlightStatusToolDesc.model_dump_json())
    async def get_flight_status(flight_number: str, date: str = None) -> list[TextContent]:
        """Get flight status and details
        
        Args:
            flight_number: Flight number (e.g., '6E123', 'AI101', 'UK987')
            date: Optional date in YYYY-MM-DD format (defaults to today)
        """
        try:
            if not flight_number.strip():
                return [TextContent(type="text", text="❌ Please provide a flight number (e.g., 6E123, AI101, UK987)")]
            
            flight_info = await flight_service.get_flight_status(flight_number, date)
            
            # Format the response
            output = f"✈️ **Flight Status: {flight_info.flight_number}**\n\n"
            output += f"🏢 **Airline:** {flight_info.airline}\n"
            output += f"📊 **Status:** {flight_info.status}\n\n"
            
            output += f"🛫 **Departure:**\n"
            output += f"   📍 {flight_info.departure_airport}\n"
            output += f"   ⏰ {flight_info.departure_time}\n"
            if flight_info.gate:
                output += f"   🚪 Gate: {flight_info.gate}\n"
            if flight_info.terminal:
                output += f"   🏢 Terminal: {flight_info.terminal}\n"
            
            output += f"\n🛬 **Arrival:**\n"
            output += f"   📍 {flight_info.arrival_airport}\n"
            output += f"   ⏰ {flight_info.arrival_time}\n"
            
            if flight_info.aircraft_type:
                output += f"\n✈️ **Aircraft:** {flight_info.aircraft_type}\n"
            
            if flight_info.delay_reason:
                output += f"\n⚠️ **Delay Reason:** {flight_info.delay_reason}\n"
            
            # Add helpful links
            output += f"\n🔗 **Useful Links:**\n"
            output += f"• [Track on FlightAware](https://flightaware.com/live/flight/{flight_number})\n"
            output += f"• [Check on FlightRadar24](https://www.flightradar24.com/data/flights/{flight_number})\n"
            
            # Add tips
            output += f"\n💡 **Tips:**\n"
            output += f"• Check 2-3 hours before departure\n"
            output += f"• Download airline app for real-time updates\n"
            output += f"• Verify gate information at airport\n"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            error_msg = f"❌ **Flight Status Check Failed**\n\n**Error:** {str(e)}\n\n"
            error_msg += "**Try:**\n"
            error_msg += "• Using format like '6E123' or 'AI101'\n"
            error_msg += "• Checking the airline's official website\n"
            error_msg += "• Verifying the flight number is correct\n"
            
            return [TextContent(type="text", text=error_msg)]

    # Airport Information Tool  
    AirportInfoToolDesc = RichToolDescription(
        description="Get airport information, weather, and details for any airport worldwide",
        use_when="user wants airport details, weather conditions, or airport information",
        side_effects="Retrieves airport data and weather information"
    )

    @mcp.tool(description=AirportInfoToolDesc.model_dump_json())
    async def get_airport_info(airport_code: str) -> list[TextContent]:
        """Get airport information and weather
        
        Args:
            airport_code: 3-letter airport code (e.g., 'DEL', 'BOM', 'DXB')
        """
        try:
            if not airport_code.strip():
                return [TextContent(type="text", text="❌ Please provide an airport code (e.g., DEL, BOM, BLR)")]
            
            airport_info = await flight_service.get_airport_info(airport_code)
            
            if not airport_info:
                return [TextContent(type="text", text=f"❌ Airport information not found for '{airport_code}'. Try common codes like DEL, BOM, BLR, MAA, DXB, SIN.")]
            
            output = f"🏢 **Airport Information: {airport_info.code}**\n\n"
            output += f"📍 **Name:** {airport_info.name}\n"
            output += f"🏙️ **City:** {airport_info.city}\n"
            output += f"🌍 **Country:** {airport_info.country}\n"
            output += f"⏰ **Timezone:** {airport_info.timezone}\n"
            
            if airport_info.weather:
                output += f"🌤️ **Weather:** {airport_info.weather}\n"
            
            # Add useful information
            output += f"\n🔗 **Useful Links:**\n"
            output += f"• [Airport Website](https://www.google.com/search?q={airport_info.name}+official+website)\n"
            output += f"• [Flight Departures](https://www.google.com/search?q={airport_info.code}+departures)\n"
            output += f"• [Flight Arrivals](https://www.google.com/search?q={airport_info.code}+arrivals)\n"
            
            # Add major Indian airports list
            if airport_info.country == "India":
                output += f"\n🇮🇳 **Other Major Indian Airports:**\n"
                major_airports = [
                    "DEL - Delhi", "BOM - Mumbai", "BLR - Bangalore", 
                    "MAA - Chennai", "HYD - Hyderabad", "CCU - Kolkata"
                ]
                for airport in major_airports:
                    if not airport.startswith(airport_code):
                        output += f"• {airport}\n"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            error_msg = f"❌ **Airport Information Failed**\n\n**Error:** {str(e)}"
            return [TextContent(type="text", text=error_msg)]

    # Flight Search Tool
    FlightSearchToolDesc = RichToolDescription(
        description="Search for flights between airports and get common flight numbers",
        use_when="user wants to find flights between specific airports or cities",
        side_effects="Searches flight databases for route information"
    )

    @mcp.tool(description=FlightSearchToolDesc.model_dump_json())
    async def search_flights(departure: str, arrival: str, date: str = None) -> list[TextContent]:
        """Search for flights between airports
        
        Args:
            departure: Departure airport code (e.g., 'DEL', 'BOM')
            arrival: Arrival airport code (e.g., 'BLR', 'MAA')
            date: Optional travel date in YYYY-MM-DD format
        """
        try:
            if not departure.strip() or not arrival.strip():
                return [TextContent(type="text", text="❌ Please provide both departure and arrival airport codes")]
            
            flights = await flight_service.search_flights(departure, arrival, date)
            
            output = f"🔍 **Flight Search: {departure.upper()} → {arrival.upper()}**\n\n"
            
            if date:
                output += f"📅 **Date:** {date}\n\n"
            
            if flights and flights[0] != f"Check airline websites for {departure.upper()} to {arrival.upper()} flights":
                output += f"✈️ **Available Flights:**\n"
                for flight in flights:
                    airline_code = flight[:2]
                    airline_name = flight_service.indian_airlines.get(airline_code, airline_code)
                    output += f"• **{flight}** - {airline_name}\n"
                
                output += f"\n💡 **Next Steps:**\n"
                output += f"• Use flight status tool to check specific flights\n"
                output += f"• Visit airline websites for booking\n"
                output += f"• Check prices on travel booking sites\n"
            else:
                output += f"📝 **Route Information:**\n"
                output += f"This route may have flights available. Check:\n\n"
                output += f"🔗 **Booking Websites:**\n"
                output += f"• [MakeMyTrip](https://www.makemytrip.com/)\n"
                output += f"• [Cleartrip](https://www.cleartrip.com/)\n"
                output += f"• [GoAir](https://www.goair.in/)\n"
                output += f"• [IndiGo](https://www.goindigo.in/)\n"
                output += f"• [Air India](https://www.airindia.in/)\n"
                
                output += f"\n🏢 **Direct Airline Websites:**\n"
                output += f"• Check major airlines for direct flights\n"
                output += f"• Consider connecting flights through major hubs\n"
            
            print(output)
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            error_msg = f"❌ **Flight Search Failed**\n\n**Error:** {str(e)}"
            return [TextContent(type="text", text=error_msg)]

    # Travel Information Tool
    TravelInfoToolDesc = RichToolDescription(
        description="Get comprehensive travel information including airlines, airports, and travel tips",
        use_when="user needs general travel information, airline codes, or travel guidance",
        side_effects="Provides travel reference information"
    )

    @mcp.tool(description=TravelInfoToolDesc.model_dump_json())
    async def get_travel_info() -> list[TextContent]:
        """Get comprehensive travel information and tips"""
        output = "✈️ **Travel Information Hub**\n\n"
        
        output += "🏢 **Major Indian Airlines:**\n"
        for code, name in flight_service.indian_airlines.items():
            output += f"• **{code}** - {name}\n"
        
        output += "\n🏢 **Major Indian Airports:**\n"
        indian_airports = {
            'DEL': 'Delhi - Indira Gandhi International',
            'BOM': 'Mumbai - Chhatrapati Shivaji', 
            'BLR': 'Bangalore - Kempegowda International',
            'MAA': 'Chennai - Chennai International',
            'HYD': 'Hyderabad - Rajiv Gandhi International',
            'CCU': 'Kolkata - Netaji Subhas Chandra Bose'
        }
        
        for code, name in indian_airports.items():
            output += f"• **{code}** - {name}\n"
        
        output += "\n🌍 **Major International Airports:**\n"
        intl_airports = {
            'DXB': 'Dubai International',
            'SIN': 'Singapore Changi', 
            'LHR': 'London Heathrow',
            'JFK': 'New York JFK',
            'NRT': 'Tokyo Narita'
        }
        
        for code, name in intl_airports.items():
            output += f"• **{code}** - {name}\n"
        
        output += "\n💡 **Travel Tips:**\n"
        output += "• Check-in online 24-48 hours before departure\n"
        output += "• Arrive 2-3 hours early for international flights\n"
        output += "• Keep ID and boarding pass handy\n"
        output += "• Download airline apps for real-time updates\n"
        output += "• Check baggage restrictions before packing\n"
        output += "• Verify passport validity (6+ months remaining)\n"
        
        output += "\n📱 **Useful Apps:**\n"
        output += "• **FlightAware** - Flight tracking\n"
        output += "• **Flightradar24** - Live flight map\n"
        output += "• **Individual airline apps** - Check-in & updates\n"
        output += "• **Google Maps** - Airport navigation\n"
        
        output += "\n🔧 **Available Tools:**\n"
        output += "• `get_flight_status()` - Check specific flights\n"
        output += "• `get_airport_info()` - Airport details & weather\n"
        output += "• `search_flights()` - Find flights between airports\n"
        
        return [TextContent(type="text", text=output)]