# parcel_tracker.py

import asyncio
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import httpx
from bs4 import BeautifulSoup
from mcp import McpError, ErrorData
from mcp.types import TextContent
from pydantic import BaseModel

class TrackingEvent(BaseModel):
    timestamp: str
    status: str
    location: str
    description: str

class TrackingResult(BaseModel):
    tracking_number: str
    courier: str
    status: str
    current_location: str
    estimated_delivery: Optional[str]
    events: List[TrackingEvent]
    last_updated: str

class ParcelTracker:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        
        # Tracking number patterns for auto-detection
        self.patterns = {
            'india_post': r'^[A-Z]{2}\d{9}IN$',
            'dtdc': r'^[A-Z0-9]{10,12}$',
            'bluedart': r'^\d{10}$',
            'fedex': r'^\d{12}$|^\d{14}$',
            'dhl': r'^\d{10}$|^\d{11}$',
            'ups': r'^1Z[A-Z0-9]{16}$',
            'aramex': r'^\d{10,11}$',
            'ecom': r'^[A-Z0-9]{10,15}$',
            'ekart': r'^[A-Z0-9]{10,15}$',
            'professional': r'^[A-Z0-9]{8,12}$'
        }

    def detect_courier(self, tracking_number: str) -> str:
        """Auto-detect courier based on tracking number pattern"""
        tracking_number = tracking_number.upper().strip()
        
        for courier, pattern in self.patterns.items():
            if re.match(pattern, tracking_number):
                return courier
        
        return 'unknown'

    async def track_india_post(self, tracking_number: str) -> TrackingResult:
        """Track India Post parcels"""
        try:
            url = "https://www.indiapost.gov.in/_layouts/15/dop.portal.tracking/trackconsignment.aspx"
            
            # First get the page to extract viewstate
            response = await self.client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            viewstate = soup.find('input', {'name': '__VIEWSTATE'})['value']
            eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})['value']
            
            # Submit tracking request
            data = {
                '__VIEWSTATE': viewstate,
                '__EVENTVALIDATION': eventvalidation,
                'ctl00$PlaceHolderMain$ucNewTracking$txtOrignlNoEnglish': tracking_number,
                'ctl00$PlaceHolderMain$ucNewTracking$btnSearch': 'Search'
            }
            
            response = await self.client.post(url, data=data)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse tracking information
            events = []
            status = "Unknown"
            current_location = "Unknown"
            
            # Look for tracking table
            table = soup.find('table', {'id': 'ctl00_PlaceHolderMain_ucNewTracking_gvResult'})
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        events.append(TrackingEvent(
                            timestamp=cells[0].text.strip(),
                            status=cells[1].text.strip(),
                            location=cells[2].text.strip(),
                            description=cells[3].text.strip()
                        ))
                
                if events:
                    status = events[0].status
                    current_location = events[0].location
            
            return TrackingResult(
                tracking_number=tracking_number,
                courier="India Post",
                status=status,
                current_location=current_location,
                estimated_delivery=None,
                events=events,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            raise Exception(f"Failed to track India Post: {str(e)}")

    async def track_dtdc(self, tracking_number: str) -> TrackingResult:
        """Track DTDC parcels"""
        try:
            url = f"https://www.dtdc.in/tracking/tracking_results.asp"
            
            data = {
                'Ttype': 'awb_no',
                'strCnno': tracking_number,
                'TrkType2': 'awb_no'
            }
            
            response = await self.client.post(url, data=data)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            events = []
            status = "Unknown"
            current_location = "Unknown"
            
            # Parse DTDC tracking table
            table = soup.find('table', {'class': 'tracking-table'})
            if not table:
                table = soup.find('table')
            
            if table:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        events.append(TrackingEvent(
                            timestamp=cells[0].text.strip(),
                            status=cells[1].text.strip(),
                            location=cells[2].text.strip() if len(cells) > 2 else "",
                            description=cells[1].text.strip()
                        ))
                
                if events:
                    status = events[0].status
                    current_location = events[0].location
            
            return TrackingResult(
                tracking_number=tracking_number,
                courier="DTDC",
                status=status,
                current_location=current_location,
                estimated_delivery=None,
                events=events,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            raise Exception(f"Failed to track DTDC: {str(e)}")

    async def track_bluedart(self, tracking_number: str) -> TrackingResult:
        """Track Blue Dart parcels"""
        try:
            url = "https://www.bluedart.com/web/guest/trackdartresult"
            
            params = {
                'trackFor': 'awb',
                'trackNo': tracking_number
            }
            
            response = await self.client.get(url, params=params)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            events = []
            status = "Unknown"
            current_location = "Unknown"
            
            # Parse Blue Dart tracking information
            tracking_div = soup.find('div', {'class': 'tracking-result'})
            if tracking_div:
                rows = tracking_div.find_all('div', {'class': 'tracking-row'})
                for row in rows:
                    date_elem = row.find('span', {'class': 'date'})
                    status_elem = row.find('span', {'class': 'status'})
                    location_elem = row.find('span', {'class': 'location'})
                    
                    if date_elem and status_elem:
                        events.append(TrackingEvent(
                            timestamp=date_elem.text.strip(),
                            status=status_elem.text.strip(),
                            location=location_elem.text.strip() if location_elem else "",
                            description=status_elem.text.strip()
                        ))
                
                if events:
                    status = events[0].status
                    current_location = events[0].location
            
            return TrackingResult(
                tracking_number=tracking_number,
                courier="Blue Dart",
                status=status,
                current_location=current_location,
                estimated_delivery=None,
                events=events,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            raise Exception(f"Failed to track Blue Dart: {str(e)}")

    async def track_fedex(self, tracking_number: str) -> TrackingResult:
        """Track FedEx parcels using web scraping"""
        try:
            url = f"https://www.fedex.com/fedextrack/?trknbr={tracking_number}"
            
            response = await self.client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            events = []
            status = "Unknown"
            current_location = "Unknown"
            
            # Parse FedEx tracking (simplified - actual implementation may need more sophisticated parsing)
            status_elem = soup.find('span', {'data-cy': 'shipmentStatus'})
            if status_elem:
                status = status_elem.text.strip()
            
            location_elem = soup.find('span', {'data-cy': 'currentLocation'})
            if location_elem:
                current_location = location_elem.text.strip()
            
            # Look for tracking events
            event_list = soup.find('div', {'data-cy': 'trackingEvents'})
            if event_list:
                event_items = event_list.find_all('div', {'class': 'tracking-event'})
                for item in event_items:
                    date_elem = item.find('span', {'class': 'date'})
                    status_elem = item.find('span', {'class': 'status'})
                    location_elem = item.find('span', {'class': 'location'})
                    
                    if date_elem and status_elem:
                        events.append(TrackingEvent(
                            timestamp=date_elem.text.strip(),
                            status=status_elem.text.strip(),
                            location=location_elem.text.strip() if location_elem else "",
                            description=status_elem.text.strip()
                        ))
            
            return TrackingResult(
                tracking_number=tracking_number,
                courier="FedEx",
                status=status,
                current_location=current_location,
                estimated_delivery=None,
                events=events,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            raise Exception(f"Failed to track FedEx: {str(e)}")

    async def track_generic_api(self, tracking_number: str, courier: str) -> TrackingResult:
        """Generic tracking using 17track API (free tier)"""
        try:
            url = "https://api.17track.net/track/v2.2/gettrackinfo"
            
            headers = {
                "17token": "YOUR_17TRACK_API_KEY",  # Get free API key from 17track.net
                "Content-Type": "application/json"
            }
            
            data = [{
                "number": tracking_number,
                "carrier": self.get_17track_carrier_code(courier)
            }]
            
            response = await self.client.post(url, json=data, headers=headers)
            result = response.json()
            
            if result.get("data") and result["data"]["accepted"]:
                track_info = result["data"]["accepted"][0]
                track_data = track_info.get("track", {})
                
                events = []
                for event in track_data.get("z1", []):
                    events.append(TrackingEvent(
                        timestamp=event.get("a", ""),
                        status=event.get("z", ""),
                        location=event.get("c", ""),
                        description=event.get("z", "")
                    ))
                
                return TrackingResult(
                    tracking_number=tracking_number,
                    courier=courier.title(),
                    status=track_data.get("e", "Unknown"),
                    current_location=events[0].location if events else "Unknown",
                    estimated_delivery=None,
                    events=events,
                    last_updated=datetime.now().isoformat()
                )
            
        except Exception as e:
            # Fallback to basic tracking
            pass
        
        return TrackingResult(
            tracking_number=tracking_number,
            courier=courier.title(),
            status="Unable to track",
            current_location="Unknown",
            estimated_delivery=None,
            events=[],
            last_updated=datetime.now().isoformat()
        )

    def get_17track_carrier_code(self, courier: str) -> int:
        """Map courier names to 17track carrier codes"""
        mapping = {
            'dhl': 45,
            'fedex': 29,
            'ups': 28,
            'usps': 8,
            'india_post': 4178,
            'dtdc': 4179,
            'bluedart': 4180,
            'aramex': 54
        }
        return mapping.get(courier, 0)

    async def track_parcel(self, tracking_number: str, courier: str = None) -> TrackingResult:
        """Main tracking function"""
        tracking_number = tracking_number.strip().upper()
        
        if not courier:
            courier = self.detect_courier(tracking_number)
        
        courier = courier.lower()
        
        try:
            if courier == 'india_post':
                return await self.track_india_post(tracking_number)
            elif courier == 'dtdc':
                return await self.track_dtdc(tracking_number)
            elif courier == 'bluedart':
                return await self.track_bluedart(tracking_number)
            elif courier == 'fedex':
                return await self.track_fedex(tracking_number)
            else:
                return await self.track_generic_api(tracking_number, courier)
                
        except Exception as e:
            return TrackingResult(
                tracking_number=tracking_number,
                courier=courier.title(),
                status=f"Tracking failed: {str(e)}",
                current_location="Unknown",
                estimated_delivery=None,
                events=[],
                last_updated=datetime.now().isoformat()
            )

def register_parcel_tracker_tools(mcp):
    """Register parcel tracking tools with MCP"""
    tracker = ParcelTracker()
    
    class RichToolDescription(BaseModel):
        description: str
        use_when: str
        side_effects: str | None

    TrackParcelToolDesc = RichToolDescription(
        description="Track parcels and packages from various courier services including India Post, DTDC, Blue Dart, FedEx, DHL, UPS, etc.",
        use_when="user wants to track a package, check delivery status, or get shipping updates",
        side_effects="Fetches real-time tracking information from courier websites"
    )

    @mcp.tool(description=TrackParcelToolDesc.model_dump_json())
    async def track_parcel(tracking_number: str, courier: str = None) -> list[TextContent]:
        """Track a parcel by tracking number"""
        try:
            result = await tracker.track_parcel(tracking_number, courier)
            
            # Format the response
            output = f"📦 **Package Tracking: {result.tracking_number}**\n\n"
            output += f"🚚 **Courier:** {result.courier}\n"
            output += f"📍 **Current Status:** {result.status}\n"
            output += f"🗺️ **Current Location:** {result.current_location}\n"
            
            if result.estimated_delivery:
                output += f"📅 **Estimated Delivery:** {result.estimated_delivery}\n"
            
            output += f"🕒 **Last Updated:** {result.last_updated}\n\n"
            
            if result.events:
                output += "📋 **Tracking History:**\n\n"
                for i, event in enumerate(result.events[:10], 1):  # Show last 10 events
                    output += f"{i}. **{event.timestamp}**\n"
                    output += f"   📍 {event.location}\n"
                    output += f"   ✅ {event.status}\n"
                    if event.description != event.status:
                        output += f"   💬 {event.description}\n"
                    output += "\n"
            else:
                output += "❌ No tracking events found.\n"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            error_msg = f"❌ **Tracking Error**\n\nFailed to track package {tracking_number}.\n\n**Error:** {str(e)}\n\nPlease check the tracking number and try again."
            return [TextContent(type="text", text=error_msg)]

    DetectCourierToolDesc = RichToolDescription(
        description="Automatically detect courier service based on tracking number format",
        use_when="user wants to identify which courier service a tracking number belongs to",
        side_effects="Analyzes tracking number pattern to identify courier"
    )

    @mcp.tool(description=DetectCourierToolDesc.model_dump_json())
    async def detect_courier_service(tracking_number: str) -> list[TextContent]:
        """Detect which courier service a tracking number belongs to"""
        try:
            detected_courier = tracker.detect_courier(tracking_number)
            
            courier_names = {
                'india_post': 'India Post',
                'dtdc': 'DTDC',
                'bluedart': 'Blue Dart',
                'fedex': 'FedEx',
                'dhl': 'DHL',
                'ups': 'UPS',
                'aramex': 'Aramex',
                'ecom': 'Ecom Express',
                'ekart': 'Ekart Logistics',
                'professional': 'Professional Couriers',
                'unknown': 'Unknown/Generic'
            }
            
            courier_name = courier_names.get(detected_courier, 'Unknown')
            
            output = f"🔍 **Courier Detection**\n\n"
            output += f"📦 **Tracking Number:** {tracking_number}\n"
            output += f"🚚 **Detected Courier:** {courier_name}\n\n"
            
            if detected_courier == 'unknown':
                output += "⚠️ Could not automatically detect courier service.\n"
                output += "You can still try tracking by specifying the courier manually.\n\n"
                output += "**Supported Couriers:**\n"
                for key, name in courier_names.items():
                    if key != 'unknown':
                        output += f"• {name}\n"
            else:
                output += f"✅ You can track this package using the '{courier_name}' service."
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            error_msg = f"❌ Error detecting courier: {str(e)}"
            return [TextContent(type="text", text=error_msg)]

    SupportedCouriersToolDesc = RichToolDescription(
        description="List all supported courier services for package tracking",
        use_when="user wants to know which courier services are supported for tracking",
        side_effects="Returns list of supported courier services"
    )

    @mcp.tool(description=SupportedCouriersToolDesc.model_dump_json())
    async def list_supported_couriers() -> list[TextContent]:
        """List all supported courier services"""
        output = "📋 **Supported Courier Services**\n\n"
        
        couriers = [
            ("🇮🇳 **Indian Couriers:**", [
                "India Post - National postal service",
                "DTDC - Domestic & international courier",
                "Blue Dart - Express delivery service",
                "Ecom Express - E-commerce logistics",
                "Ekart Logistics - Flipkart logistics",
                "Professional Couriers - Regional service"
            ]),
            ("🌍 **International Couriers:**", [
                "FedEx - Global express delivery",
                "DHL - International shipping",
                "UPS - United Parcel Service",
                "Aramex - Middle East & international"
            ])
        ]
        
        for category, services in couriers:
            output += f"{category}\n"
            for service in services:
                output += f"• {service}\n"
            output += "\n"
        
        output += "💡 **Tips:**\n"
        output += "• Most tracking numbers are auto-detected\n"
        output += "• You can specify courier manually if auto-detection fails\n"
        output += "• Tracking history shows last 10 events\n"
        output += "• Real-time updates from courier websites\n"
        
        return [TextContent(type="text", text=output)]