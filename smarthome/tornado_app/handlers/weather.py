"""
API handler for weather service.
"""

import json
import re
from ..models import House
from ..database import async_session_maker
from ..services.weather_service import WeatherService
from .base import BaseAPIHandler


class WeatherHandler(BaseAPIHandler):
    """GET /api/weather/{house_id} - Get weather for a house."""

    async def get(self, house_id):
        """Get weather based on house address."""
        async with async_session_maker() as session:
            # Retrieve la maison
            house = await session.get(House, int(house_id))
            if not house:
                self.write_error_json("House not found", 404)
                return

            if not house.address:
                self.write_error_json("No address defined for this house", 400)
                return

            # Extract city name from address
            # Ex: "Campus, 97157 Pointe-à-Pitre, Guadeloupe"
            # -> "Pointe-à-Pitre"
            address_parts = house.address.split(",")
            # By default, use the complete address
            city_name = house.address

            # Find the part containing a city
            # (usually before country)
            if len(address_parts) >= 2:
                # Take the second-to-last part
                if len(address_parts) >= 2:
                    city_name = address_parts[-2].strip()
                else:
                    city_name = address_parts[-1].strip()
                # Enlever les codes postaux
                city_name = re.sub(r"\b\d{5}\b", "", city_name).strip()

            # Get coordinates
            coords = await WeatherService.get_coordinates(city_name)
            if not coords:
                self.write_error_json(f"Could not geocode address: {city_name}", 400)
                return

            # Get weather
            weather = await WeatherService.get_weather(
                coords["latitude"], coords["longitude"]
            )
            if not weather:
                self.write_error_json("Could not fetch weather data", 500)
                return

            # Add location
            weather["location"] = {
                "city": coords.get("name", ""),
                "admin1": coords.get("admin1", ""),
                "country_code": coords.get("country_code", ""),
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
            }

            self.write_json(weather)


class ValidateAddressHandler(BaseAPIHandler):
    """POST /api/weather/validate-address - Validate an address."""

    async def post(self):
        """Check if an address can be geolocated."""
        try:
            data = json.loads(self.request.body)
            address = data.get("address", "").strip()

            if not address:
                self.write_error_json("Address is required", 400)
                return

            # Extract city name from address
            address_parts = address.split(",")
            city_name = address

            if len(address_parts) >= 2:
                city_name = address_parts[-2].strip()
                # Enlever les codes postaux
                city_name = re.sub(r"\b\d{5}\b", "", city_name).strip()

            # Attempt to geocode
            coords = await WeatherService.get_coordinates(city_name)

            if coords:
                location_name = coords.get("name", "")
                if coords.get("admin1"):
                    location_name += f", {coords['admin1']}"
                if coords.get("country_code"):
                    location_name += f" ({coords['country_code']})"

                self.write_json(
                    {
                        "valid": True,
                        "location": location_name,
                        "coordinates": {
                            "latitude": coords["latitude"],
                            "longitude": coords["longitude"],
                        },
                    }
                )
            else:
                self.write_json(
                    {"valid": False, "error": "Address not recognized by geocoding API"}
                )

        except Exception as e:
            self.write_error_json(f"Validation error: {str(e)}", 500)
