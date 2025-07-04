# map_services.py

import asyncio
import json
import math
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import httpx
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from mcp import McpError, ErrorData
from mcp.types import TextContent
from pydantic import BaseModel
from config import OPENCAGE_API_KEY, GOOGLE_MAPS_API_KEY

class LocationData(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    place_type: str
    country: str
    state: str
    city: str

class DirectionsData(BaseModel):
    distance: str
    duration: str
    steps: List[str]
    start_location: LocationData
    end_location: LocationData

class NearbyPlace(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    distance: str
    place_type: str
    rating: Optional[float] = None
    phone: Optional[str] = None

class MapServices:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.geocoder = Nominatim(user_agent="map_services_tool_v1.0")
        
        # API keys - Google is the most accurate
        self.google_api_key = GOOGLE_MAPS_API_KEY  # Get from Google Cloud Console
        self.opencage_api_key = OPENCAGE_API_KEY  # Backup option
        self.openweather_api_key = "YOUR_OPENWEATHER_API_KEY"
        
    async def geocode_location(self, location: str) -> LocationData:
        """Convert address/place name to coordinates using Google Maps API"""
        try:
            # Try Google Geocoding API first (most accurate)
            if self.google_api_key != "YOUR_GOOGLE_MAPS_API_KEY":
                url = "https://maps.googleapis.com/maps/api/geocode/json"
                params = {
                    "address": location,
                    "key": self.google_api_key,
                    "language": "en"
                }
                
                response = await self.client.get(url, params=params)
                data = response.json()
                
                if data.get("status") == "OK" and data.get("results"):
                    result = data["results"][0]
                    geometry = result["geometry"]["location"]
                    components = result["address_components"]
                    
                    # Extract address components
                    country = ""
                    state = ""
                    city = ""
                    
                    for component in components:
                        types = component["types"]
                        if "country" in types:
                            country = component["long_name"]
                        elif "administrative_area_level_1" in types:
                            state = component["long_name"]
                        elif "locality" in types or "administrative_area_level_2" in types:
                            city = component["long_name"]
                    
                    # Determine place type
                    place_types = result.get("types", [])
                    place_type = place_types[0] if place_types else "unknown"
                    
                    return LocationData(
                        name=result["formatted_address"],
                        address=result["formatted_address"],
                        latitude=geometry["lat"],
                        longitude=geometry["lng"],
                        place_type=place_type.replace("_", " "),
                        country=country,
                        state=state,
                        city=city
                    )
                elif data.get("status") == "ZERO_RESULTS":
                    raise Exception(f"Location '{location}' not found")
                elif data.get("status") == "REQUEST_DENIED":
                    raise Exception("Google API key invalid or quota exceeded")
                else:
                    raise Exception(f"Google API error: {data.get('status', 'Unknown error')}")
            
            # Fallback to OpenCage (still better than Nominatim)
            if self.opencage_api_key != "YOUR_OPENCAGE_API_KEY":
                url = f"https://api.opencagedata.com/geocode/v1/json"
                params = {
                    "q": location,
                    "key": self.opencage_api_key,
                    "limit": 1,
                    "language": "en"
                }
                
                response = await self.client.get(url, params=params)
                data = response.json()
                
                if data.get("results"):
                    result = data["results"][0]
                    components = result["components"]
                    geometry = result["geometry"]
                    
                    return LocationData(
                        name=result.get("formatted", location),
                        address=result.get("formatted", ""),
                        latitude=geometry["lat"],
                        longitude=geometry["lng"],
                        place_type=components.get("_type", "unknown"),
                        country=components.get("country", ""),
                        state=components.get("state", ""),
                        city=components.get("city", components.get("town", components.get("village", "")))
                    )
            
            # Last resort: Nominatim (free but less accurate)
            result = self.geocoder.geocode(location, exactly_one=True, timeout=10)
            if result:
                raw = result.raw
                
                return LocationData(
                    name=result.address,
                    address=result.address,
                    latitude=result.latitude,
                    longitude=result.longitude,
                    place_type=raw.get("type", "unknown"),
                    country=raw.get("address", {}).get("country", ""),
                    state=raw.get("address", {}).get("state", ""),
                    city=raw.get("address", {}).get("city", raw.get("address", {}).get("town", ""))
                )
            
            raise Exception(f"Location '{location}' not found in any geocoding service")
            
        except Exception as e:
            if "quota" in str(e).lower() or "key" in str(e).lower():
                raise Exception(f"API key issue: {str(e)}")
            raise Exception(f"Geocoding failed: {str(e)}")

    async def reverse_geocode(self, latitude: float, longitude: float) -> LocationData:
        """Convert coordinates to address using Google Maps API"""
        try:
            # Try Google Reverse Geocoding API first (most accurate)
            if self.google_api_key != "YOUR_GOOGLE_MAPS_API_KEY":
                url = "https://maps.googleapis.com/maps/api/geocode/json"
                params = {
                    "latlng": f"{latitude},{longitude}",
                    "key": self.google_api_key,
                    "language": "en"
                }
                
                response = await self.client.get(url, params=params)
                data = response.json()
                
                if data.get("status") == "OK" and data.get("results"):
                    result = data["results"][0]
                    components = result["address_components"]
                    
                    # Extract address components
                    country = ""
                    state = ""
                    city = ""
                    
                    for component in components:
                        types = component["types"]
                        if "country" in types:
                            country = component["long_name"]
                        elif "administrative_area_level_1" in types:
                            state = component["long_name"]
                        elif "locality" in types or "administrative_area_level_2" in types:
                            city = component["long_name"]
                    
                    place_types = result.get("types", [])
                    place_type = place_types[0] if place_types else "coordinate"
                    
                    return LocationData(
                        name=result["formatted_address"],
                        address=result["formatted_address"],
                        latitude=latitude,
                        longitude=longitude,
                        place_type=place_type.replace("_", " "),
                        country=country,
                        state=state,
                        city=city
                    )
                elif data.get("status") == "REQUEST_DENIED":
                    raise Exception("Google API key invalid or quota exceeded")
            
            # Fallback to OpenCage
            if self.opencage_api_key != "YOUR_OPENCAGE_API_KEY":
                url = f"https://api.opencagedata.com/geocode/v1/json"
                params = {
                    "q": f"{latitude},{longitude}",
                    "key": self.opencage_api_key,
                    "language": "en"
                }
                
                response = await self.client.get(url, params=params)
                data = response.json()
                
                if data.get("results"):
                    result = data["results"][0]
                    components = result["components"]
                    
                    return LocationData(
                        name=result.get("formatted", f"{latitude}, {longitude}"),
                        address=result.get("formatted", ""),
                        latitude=latitude,
                        longitude=longitude,
                        place_type=components.get("_type", "coordinate"),
                        country=components.get("country", ""),
                        state=components.get("state", ""),
                        city=components.get("city", components.get("town", ""))
                    )
            
            # Last resort: Nominatim
            result = self.geocoder.reverse((latitude, longitude), exactly_one=True, timeout=10)
            if result:
                raw = result.raw
                return LocationData(
                    name=result.address,
                    address=result.address,
                    latitude=latitude,
                    longitude=longitude,
                    place_type=raw.get("type", "coordinate"),
                    country=raw.get("address", {}).get("country", ""),
                    state=raw.get("address", {}).get("state", ""),
                    city=raw.get("address", {}).get("city", "")
                )
            
            raise Exception("Could not reverse geocode coordinates")
            
        except Exception as e:
            if "quota" in str(e).lower() or "key" in str(e).lower():
                raise Exception(f"API key issue: {str(e)}")
            raise Exception(f"Reverse geocoding failed: {str(e)}")

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, str]:
        """Calculate distance between two coordinates"""
        try:
            # Using geodesic distance (more accurate)
            distance = geodesic((lat1, lon1), (lat2, lon2))
            
            km = distance.kilometers
            miles = distance.miles
            
            if km < 1:
                distance_str = f"{int(distance.meters)} meters"
            elif km < 10:
                distance_str = f"{km:.1f} km ({miles:.1f} miles)"
            else:
                distance_str = f"{int(km)} km ({int(miles)} miles)"
            
            return km, distance_str
            
        except Exception as e:
            raise Exception(f"Distance calculation failed: {str(e)}")

    async def get_directions(self, from_location: str, to_location: str, mode: str = "driving") -> DirectionsData:
        """Get directions between two locations"""
        try:
            # Geocode both locations
            start_loc = await self.geocode_location(from_location)
            end_loc = await self.geocode_location(to_location)
            
            # Calculate direct distance
            km_distance, distance_str = self.calculate_distance(
                start_loc.latitude, start_loc.longitude,
                end_loc.latitude, end_loc.longitude
            )
            
            # Estimate travel time based on mode
            if mode == "driving":
                # Average speed: 50 km/h for mixed roads
                hours = km_distance / 50
                duration = f"{int(hours)}h {int((hours % 1) * 60)}m" if hours >= 1 else f"{int(hours * 60)}m"
            elif mode == "walking":
                # Average walking speed: 5 km/h
                hours = km_distance / 5
                duration = f"{int(hours)}h {int((hours % 1) * 60)}m" if hours >= 1 else f"{int(hours * 60)}m"
            elif mode == "cycling":
                # Average cycling speed: 15 km/h
                hours = km_distance / 15
                duration = f"{int(hours)}h {int((hours % 1) * 60)}m" if hours >= 1 else f"{int(hours * 60)}m"
            else:
                duration = "Unknown"
            
            # Generate basic directions
            bearing = self.calculate_bearing(
                start_loc.latitude, start_loc.longitude,
                end_loc.latitude, end_loc.longitude
            )
            
            direction = self.bearing_to_direction(bearing)
            
            steps = [
                f"Start from {start_loc.name}",
                f"Head {direction} towards {end_loc.name}",
                f"Continue for {distance_str}",
                f"Arrive at {end_loc.name}"
            ]
            
            return DirectionsData(
                distance=distance_str,
                duration=duration,
                steps=steps,
                start_location=start_loc,
                end_location=end_loc
            )
            
        except Exception as e:
            raise Exception(f"Failed to get directions: {str(e)}")

    def calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing from point 1 to point 2"""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing

    def bearing_to_direction(self, bearing: float) -> str:
        """Convert bearing to compass direction"""
        directions = [
            "North", "Northeast", "East", "Southeast",
            "South", "Southwest", "West", "Northwest"
        ]
        
        index = round(bearing / 45) % 8
        return directions[index]

    def normalize_place_type(self, place_type: str) -> str:
        """Normalize place type to standard format"""
        place_type = place_type.lower().strip()
        
        # Mapping variations to standard types
        place_type_mappings = {
            # Gas stations / Petrol pumps
            "petrol_pump": "gas_station",
            "petrol pump": "gas_station", 
            "gas_pump": "gas_station",
            "gas pump": "gas_station",
            "fuel_station": "gas_station",
            "fuel station": "gas_station",
            "petrol_station": "gas_station",
            "petrol station": "gas_station",
            "filling_station": "gas_station",
            "filling station": "gas_station",
            
            # Restaurants
            "food": "restaurant",
            "dining": "restaurant",
            "eatery": "restaurant",
            "restaurants": "restaurant",
            
            # Medical
            "medical": "hospital",
            "clinic": "hospital",
            "doctor": "hospital",
            "health": "hospital",
            "medicine": "pharmacy",
            "chemist": "pharmacy",
            "drug_store": "pharmacy",
            "drug store": "pharmacy",
            
            # Financial
            "banks": "bank",
            "banking": "bank",
            "atms": "atm",
            "cash": "atm",
            
            # Shopping
            "mall": "shopping",
            "store": "shopping",
            "shop": "shopping",
            "market": "shopping",
            "supermarket": "shopping",
            "grocery": "shopping",
            
            # Accommodation
            "hotels": "hotel",
            "lodging": "hotel",
            "accommodation": "hotel",
            "motel": "hotel",
            
            # Education
            "schools": "school",
            "education": "school",
            "college": "school",
            "university": "school",
            
            # Coffee/Cafe
            "coffee": "cafe",
            "coffee_shop": "cafe",
            "coffee shop": "cafe",
            
            # Emergency
            "police_station": "police",
            "police station": "police",
            "fire_department": "fire_station",
            "fire department": "fire_station",
        }
        
        return place_type_mappings.get(place_type, place_type)

    async def find_nearby_places_google(self, location: str, place_type: str, radius: int) -> List[NearbyPlace]:
        """Find nearby places using Google Places API"""
        try:
            if self.google_api_key == "YOUR_GOOGLE_MAPS_API_KEY":
                return []
            
            # First geocode the location
            center_location = await self.geocode_location(location)
            
            # Google Places API
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            
            # Map our place types to Google Places types
            google_place_types = {
                "restaurant": "restaurant",
                "hospital": "hospital", 
                "pharmacy": "pharmacy",
                "bank": "bank",
                "atm": "atm",
                "gas_station": "gas_station",
                "school": "school",
                "hotel": "lodging",
                "shopping": "shopping_mall",
                "cafe": "cafe",
                "police": "police",
                "fire_station": "fire_station"
            }
            
            google_type = google_place_types.get(place_type, place_type)
            
            params = {
                "location": f"{center_location.latitude},{center_location.longitude}",
                "radius": radius,
                "type": google_type,
                "key": self.google_api_key
            }
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            nearby_places = []
            for place in data.get("results", [])[:20]:
                geometry = place["geometry"]["location"]
                
                # Calculate distance
                _, distance_str = self.calculate_distance(
                    center_location.latitude, center_location.longitude,
                    geometry["lat"], geometry["lng"]
                )
                
                # Get place details
                name = place.get("name", f"Unnamed {place_type}")
                address = place.get("vicinity", "Address not available")
                rating = place.get("rating")
                
                nearby_places.append(NearbyPlace(
                    name=name,
                    address=address,
                    latitude=geometry["lat"],
                    longitude=geometry["lng"],
                    distance=distance_str,
                    place_type=place_type,
                    phone=None,  # Need Place Details API for phone
                    rating=rating
                ))
            
            # Sort by distance
            nearby_places.sort(key=lambda x: float(x.distance.split()[0]))
            return nearby_places[:10]
            
        except Exception as e:
            return []  # Fallback to OSM if Google fails

    async def find_nearby_places(self, location: str, place_type: str = "restaurant", radius: int = 5000) -> List[NearbyPlace]:
        """Find nearby places of specific type"""
        try:
            # Normalize the place type
            normalized_type = self.normalize_place_type(place_type)
            
            # First geocode the location
            center_location = await self.geocode_location(location)
            
            # Try Google Places API first (if available)
            google_results = await self.find_nearby_places_google(location, normalized_type, radius)
            if google_results:
                return google_results
            
            # Fallback to Overpass API (OpenStreetMap)
            overpass_url = "https://overpass-api.de/api/interpreter"
            
            # Enhanced mapping with multiple tags per place type
            osm_tags = {
                "restaurant": ["amenity=restaurant", "amenity=fast_food"],
                "hospital": ["amenity=hospital", "amenity=clinic"],
                "pharmacy": ["amenity=pharmacy"],
                "bank": ["amenity=bank"],
                "atm": ["amenity=atm"],
                "gas_station": ["amenity=fuel"],
                "school": ["amenity=school", "amenity=college", "amenity=university"],
                "hotel": ["tourism=hotel", "tourism=motel", "tourism=guest_house"],
                "shopping": ["shop", "amenity=marketplace"],
                "cafe": ["amenity=cafe"],
                "police": ["amenity=police"],
                "fire_station": ["amenity=fire_station"]
            }
            
            tags = osm_tags.get(normalized_type, [f"amenity={normalized_type}"])
            
            # Build query with multiple tags
            tag_queries = []
            for tag in tags:
                tag_queries.append(f"node[{tag}](around:{radius},{center_location.latitude},{center_location.longitude});")
                tag_queries.append(f"way[{tag}](around:{radius},{center_location.latitude},{center_location.longitude});")
                tag_queries.append(f"relation[{tag}](around:{radius},{center_location.latitude},{center_location.longitude});")
            
            query = f"""
            [out:json][timeout:25];
            (
              {' '.join(tag_queries)}
            );
            out center meta;
            """
            
            response = await self.client.post(overpass_url, data=query)
            data = response.json()
            
            nearby_places = []
            seen_locations = set()  # Avoid duplicates
            
            for element in data.get("elements", [])[:30]:  # Get more results to filter
                tags = element.get("tags", {})
                
                # Get coordinates
                if element["type"] == "node":
                    lat, lon = element["lat"], element["lon"]
                else:
                    # For ways and relations, use center
                    center = element.get("center", {})
                    if not center:
                        continue
                    lat, lon = center["lat"], center["lon"]
                
                # Skip duplicates (same location)
                location_key = f"{lat:.6f},{lon:.6f}"
                if location_key in seen_locations:
                    continue
                seen_locations.add(location_key)
                
                # Calculate distance
                _, distance_str = self.calculate_distance(
                    center_location.latitude, center_location.longitude,
                    lat, lon
                )
                
                name = tags.get("name", f"Unnamed {place_type}")
                address = self.construct_address(tags)
                
                nearby_places.append(NearbyPlace(
                    name=name,
                    address=address,
                    latitude=lat,
                    longitude=lon,
                    distance=distance_str,
                    place_type=place_type,
                    phone=tags.get("phone"),
                    rating=None  # OSM doesn't have ratings
                ))
            
            # Sort by distance
            nearby_places.sort(key=lambda x: float(x.distance.split()[0]))
            
            return nearby_places[:10]  # Return top 10
            
        except Exception as e:
            raise Exception(f"Failed to find nearby places: {str(e)}")

    def construct_address(self, tags: dict) -> str:
        """Construct address from OSM tags"""
        address_parts = []
        
        if tags.get("addr:housenumber"):
            address_parts.append(tags["addr:housenumber"])
        if tags.get("addr:street"):
            address_parts.append(tags["addr:street"])
        if tags.get("addr:city"):
            address_parts.append(tags["addr:city"])
        if tags.get("addr:postcode"):
            address_parts.append(tags["addr:postcode"])
        
        return ", ".join(address_parts) if address_parts else "Address not available"

    async def get_elevation(self, latitude: float, longitude: float) -> dict:
        """Get elevation data for coordinates"""
        try:
            # Using Open-Elevation API (free)
            url = "https://api.open-elevation.com/api/v1/lookup"
            
            data = {
                "locations": [{"latitude": latitude, "longitude": longitude}]
            }
            
            response = await self.client.post(url, json=data)
            result = response.json()
            
            if result.get("results"):
                elevation = result["results"][0]["elevation"]
                return {
                    "elevation_meters": elevation,
                    "elevation_feet": round(elevation * 3.28084),
                    "coordinates": f"{latitude}, {longitude}"
                }
            
            raise Exception("Elevation data not available")
            
        except Exception as e:
            raise Exception(f"Failed to get elevation: {str(e)}")

def register_map_services_tools(mcp):
    """Register map services tools with MCP"""
    map_service = MapServices()
    
    class RichToolDescription(BaseModel):
        description: str
        use_when: str
        side_effects: str | None

    # Location Search Tool
    LocationSearchToolDesc = RichToolDescription(
        description="Search for locations, get coordinates, and address information",
        use_when="user wants to find a place, get coordinates, or search for an address",
        side_effects="Queries geocoding services to find location data"
    )

    @mcp.tool(description=LocationSearchToolDesc.model_dump_json())
    async def search_location(location: str) -> list[TextContent]:
        """Search for a location and get detailed information"""
        try:
            location_data = await map_service.geocode_location(location)
            
            output = f"📍 **Location Found: {location_data.name}**\n\n"
            output += f"🏠 **Address:** {location_data.address}\n"
            output += f"🌍 **Coordinates:** {location_data.latitude:.6f}, {location_data.longitude:.6f}\n"
            output += f"🏷️ **Type:** {location_data.place_type.title()}\n"
            
            if location_data.city:
                output += f"🏙️ **City:** {location_data.city}\n"
            if location_data.state:
                output += f"🗺️ **State:** {location_data.state}\n"
            if location_data.country:
                output += f"🇮🇳 **Country:** {location_data.country}\n"
            
            # Add Google Maps link
            maps_url = f"https://www.google.com/maps?q={location_data.latitude},{location_data.longitude}"
            output += f"\n🗺️ **[View on Google Maps]({maps_url})**"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            error_msg = f"❌ **Location Search Failed**\n\nCould not find '{location}'.\n\n**Error:** {str(e)}"
            return [TextContent(type="text", text=error_msg)]

    # Reverse Geocoding Tool
    ReverseGeocodeToolDesc = RichToolDescription(
        description="Convert coordinates (latitude, longitude) to address and location information",
        use_when="user provides coordinates and wants to know the address or place name",
        side_effects="Queries reverse geocoding services"
    )

    @mcp.tool(description=ReverseGeocodeToolDesc.model_dump_json())
    async def reverse_geocode_coordinates(latitude: float, longitude: float) -> list[TextContent]:
        """Convert coordinates to address"""
        try:
            location_data = await map_service.reverse_geocode(latitude, longitude)
            
            output = f"📍 **Address for Coordinates**\n\n"
            output += f"🌍 **Coordinates:** {latitude:.6f}, {longitude:.6f}\n"
            output += f"🏠 **Address:** {location_data.address}\n"
            output += f"🏷️ **Place Type:** {location_data.place_type.title()}\n"
            
            if location_data.city:
                output += f"🏙️ **City:** {location_data.city}\n"
            if location_data.state:
                output += f"🗺️ **State:** {location_data.state}\n"
            if location_data.country:
                output += f"🇮🇳 **Country:** {location_data.country}\n"
            
            # Add Google Maps link
            maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
            output += f"\n🗺️ **[View on Google Maps]({maps_url})**"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            error_msg = f"❌ **Reverse Geocoding Failed**\n\n**Error:** {str(e)}"
            return [TextContent(type="text", text=error_msg)]

    # Distance Calculator Tool
    DistanceCalculatorToolDesc = RichToolDescription(
        description="Calculate distance between two locations",
        use_when="user wants to know the distance between two places",
        side_effects="Calculates geographic distance using geodesic formulas"
    )

    @mcp.tool(description=DistanceCalculatorToolDesc.model_dump_json())
    async def calculate_distance_between_locations(location1: str, location2: str) -> list[TextContent]:
        """Calculate distance between two locations"""
        try:
            # Geocode both locations
            loc1 = await map_service.geocode_location(location1)
            loc2 = await map_service.geocode_location(location2)
            
            # Calculate distance
            km_distance, distance_str = map_service.calculate_distance(
                loc1.latitude, loc1.longitude,
                loc2.latitude, loc2.longitude
            )
            
            # Calculate bearing
            bearing = map_service.calculate_bearing(
                loc1.latitude, loc1.longitude,
                loc2.latitude, loc2.longitude
            )
            direction = map_service.bearing_to_direction(bearing)
            
            output = f"📏 **Distance Calculation**\n\n"
            output += f"📍 **From:** {loc1.name}\n"
            output += f"📍 **To:** {loc2.name}\n\n"
            output += f"📐 **Distance:** {distance_str}\n"
            output += f"🧭 **Direction:** {direction} ({bearing:.1f}°)\n"
            
            # Estimate travel times
            driving_time = km_distance / 50  # 50 km/h average
            walking_time = km_distance / 5   # 5 km/h average
            
            output += f"\n⏱️ **Estimated Travel Times:**\n"
            if driving_time >= 1:
                output += f"🚗 **Driving:** {int(driving_time)}h {int((driving_time % 1) * 60)}m\n"
            else:
                output += f"🚗 **Driving:** {int(driving_time * 60)}m\n"
            
            if walking_time >= 1:
                output += f"🚶 **Walking:** {int(walking_time)}h {int((walking_time % 1) * 60)}m\n"
            else:
                output += f"🚶 **Walking:** {int(walking_time * 60)}m\n"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            error_msg = f"❌ **Distance Calculation Failed**\n\n**Error:** {str(e)}"
            return [TextContent(type="text", text=error_msg)]

    # Directions Tool
    DirectionsToolDesc = RichToolDescription(
        description="Get directions between two locations with step-by-step instructions",
        use_when="user wants directions, route planning, or navigation instructions",
        side_effects="Calculates route and provides navigation instructions"
    )

    @mcp.tool(description=DirectionsToolDesc.model_dump_json())
    async def get_directions_between_locations(
        from_location: str, 
        to_location: str, 
        travel_mode: str = "driving"
    ) -> list[TextContent]:
        """Get directions between two locations"""
        try:
            directions = await map_service.get_directions(from_location, to_location, travel_mode)
            
            output = f"🗺️ **Directions: {from_location} → {to_location}**\n\n"
            output += f"📏 **Distance:** {directions.distance}\n"
            output += f"⏱️ **Duration:** {directions.duration}\n"
            output += f"🚗 **Mode:** {travel_mode.title()}\n\n"
            
            output += "📋 **Step-by-Step Directions:**\n\n"
            for i, step in enumerate(directions.steps, 1):
                output += f"{i}. {step}\n"
            
            # Add map links
            start_coords = f"{directions.start_location.latitude},{directions.start_location.longitude}"
            end_coords = f"{directions.end_location.latitude},{directions.end_location.longitude}"
            
            directions_url = f"https://www.google.com/maps/dir/{start_coords}/{end_coords}"
            output += f"\n🗺️ **[Open in Google Maps]({directions_url})**"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            error_msg = f"❌ **Directions Failed**\n\n**Error:** {str(e)}"
            return [TextContent(type="text", text=error_msg)]

    # Nearby Places Tool
    NearbyPlacesToolDesc = RichToolDescription(
        description="Find nearby places like restaurants, hospitals, ATMs, gas stations, etc.",
        use_when="user wants to find nearby services, amenities, or points of interest",
        side_effects="Searches OpenStreetMap database for nearby places"
    )

    @mcp.tool(description=NearbyPlacesToolDesc.model_dump_json())
    async def find_nearby_places(
        location: str, 
        place_type: str = "restaurant", 
        radius_km: int = 5
    ) -> list[TextContent]:
        """Find nearby places of a specific type"""
        try:
            radius_meters = radius_km * 1000
            nearby_places = await map_service.find_nearby_places(location, place_type, radius_meters)
            
            if not nearby_places:
                return [TextContent(type="text", text=f"❌ No {place_type}s found within {radius_km}km of {location}")]
            
            output = f"📍 **Nearby {place_type.title()}s near {location}**\n\n"
            output += f"🔍 **Search radius:** {radius_km}km\n"
            output += f"📊 **Found {len(nearby_places)} places**\n\n"
            
            for i, place in enumerate(nearby_places, 1):
                output += f"**{i}. {place.name}**\n"
                output += f"   📍 {place.address}\n"
                output += f"   📏 {place.distance} away\n"
                
                if place.phone:
                    output += f"   📞 {place.phone}\n"
                
                # Add Google Maps link
                maps_url = f"https://www.google.com/maps?q={place.latitude},{place.longitude}"
                output += f"   🗺️ [View on Map]({maps_url})\n\n"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            error_msg = f"❌ **Nearby Search Failed**\n\n**Error:** {str(e)}"
            return [TextContent(type="text", text=error_msg)]

    # Elevation Tool
    ElevationToolDesc = RichToolDescription(
        description="Get elevation/altitude data for a location or coordinates",
        use_when="user wants to know the elevation or altitude of a place",
        side_effects="Queries elevation services for geographic data"
    )

    @mcp.tool(description=ElevationToolDesc.model_dump_json())
    async def get_location_elevation(location: str = None, latitude: float = None, longitude: float = None) -> list[TextContent]:
        """Get elevation data for a location"""
        try:
            if location:
                # Geocode the location first
                location_data = await map_service.geocode_location(location)
                lat, lon = location_data.latitude, location_data.longitude
                place_name = location_data.name
            elif latitude is not None and longitude is not None:
                lat, lon = latitude, longitude
                place_name = f"Coordinates {lat:.6f}, {lon:.6f}"
            else:
                raise Exception("Please provide either a location name or coordinates")
            
            elevation_data = await map_service.get_elevation(lat, lon)
            
            output = f"⛰️ **Elevation Data**\n\n"
            output += f"📍 **Location:** {place_name}\n"
            output += f"🌍 **Coordinates:** {lat:.6f}, {lon:.6f}\n"
            output += f"📏 **Elevation:** {elevation_data['elevation_meters']} meters ({elevation_data['elevation_feet']} feet)\n"
            
            # Add context
            if elevation_data['elevation_meters'] > 2500:
                output += f"🏔️ **Category:** High altitude location\n"
            elif elevation_data['elevation_meters'] > 1000:
                output += f"🏞️ **Category:** Moderate altitude location\n"
            elif elevation_data['elevation_meters'] > 500:
                output += f"🌄 **Category:** Elevated location\n"
            else:
                output += f"🌊 **Category:** Low altitude/sea level location\n"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            error_msg = f"❌ **Elevation Query Failed**\n\n**Error:** {str(e)}"
            return [TextContent(type="text", text=error_msg)]

    # Map Services Info Tool
    MapServicesInfoToolDesc = RichToolDescription(
        description="Get information about available map services and place types",
        use_when="user wants to know what map services are available or what place types can be searched",
        side_effects="Returns information about tool capabilities"
    )

    @mcp.tool(description=MapServicesInfoToolDesc.model_dump_json())
    async def get_map_services_info() -> list[TextContent]:
        """Get information about available map services"""
        output = "🗺️ **Map Services Available**\n\n"
        
        output += "🔧 **Available Tools:**\n"
        output += "• **Location Search** - Find places and get coordinates\n"
        output += "• **Reverse Geocoding** - Convert coordinates to addresses\n"
        output += "• **Distance Calculator** - Calculate distances between locations\n"
        output += "• **Directions** - Get step-by-step navigation\n"
        output += "• **Nearby Places** - Find services and amenities nearby\n"
        output += "• **Elevation Data** - Get altitude information\n\n"
        
        output += "🏪 **Supported Place Types for Nearby Search:**\n"
        place_types = [
            "restaurant", "hospital", "pharmacy", "bank", "atm",
            "gas_station", "school", "hotel", "shopping", "cafe",
            "police", "fire_station"
        ]
        
        for place_type in place_types:
            output += f"• {place_type.replace('_', ' ').title()}\n"
        
        output += "\n🚗 **Supported Travel Modes:**\n"
        output += "• Driving (default)\n"
        output += "• Walking\n"
        output += "• Cycling\n\n"
        
        output += "💡 **Tips:**\n"
        output += "• All locations support both addresses and place names\n"
        output += "• Coordinates should be in decimal degrees format\n"
        output += "• Distance calculations use geodesic (great circle) formulas\n"
        output += "• Elevation data comes from global elevation models\n"
        output += "• All results include Google Maps links for easy viewing\n"
        
        return [TextContent(type="text", text=output)]