"""
Service météo utilisant l'API Open-Meteo (gratuite, pas besoin de clé API)
"""

import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime


class WeatherService:
    """Service pour récupérer les données météo en temps réel"""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

    @staticmethod
    async def get_coordinates(address: str) -> Optional[Dict[str, float]]:
        """
        Obtenir les coordonnées GPS à partir d'une adresse.

        Args:
            address: Adresse complète ou ville

        Returns:
            Dict avec 'latitude' et 'longitude', ou None si non trouvé
        """
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "name": address,
                    "count": 1,
                    "language": "fr",
                    "format": "json",
                }

                async with session.get(
                    WeatherService.GEOCODING_URL, params=params  # type: ignore
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("results") and len(data["results"]) > 0:
                            result = data["results"][0]
                            return {
                                "latitude": result["latitude"],
                                "longitude": result["longitude"],
                                "name": result.get("name", ""),
                                "admin1": result.get("admin1", ""),
                                "country_code": result.get("country_code", ""),
                            }
            return None
        except Exception as e:
            print(f"[Weather] Error getting coordinates: {e}")
            import traceback

            traceback.print_exc()
            return None

    @staticmethod
    async def get_weather(
        latitude: float, longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Récupérer les données météo actuelles.

        Args:
            latitude: Latitude GPS
            longitude: Longitude GPS

        Returns:
            Dict avec les données météo, ou None si erreur
        """
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": [
                        "temperature_2m",
                        "relative_humidity_2m",
                        "apparent_temperature",
                        "precipitation",
                        "rain",
                        "weather_code",
                        "cloud_cover",
                        "wind_speed_10m",
                        "wind_direction_10m",
                    ],
                    "hourly": "visibility",
                    "timezone": "auto",
                }

                async with session.get(
                    WeatherService.BASE_URL, params=params  # type: ignore
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        current = data.get("current", {})

                        # Calculer la luminosité estimée (en lux)
                        # Basé sur l'heure, couverture nuageuse et code météo
                        luminosity = WeatherService._estimate_luminosity(
                            current.get("cloud_cover", 0),
                            current.get("weather_code", 0),
                        )

                        weather_code = current.get("weather_code", 0)

                        return {
                            "temperature": current.get("temperature_2m"),
                            "apparent_temperature": current.get("apparent_temperature"),
                            "humidity": current.get("relative_humidity_2m"),
                            "precipitation": current.get("precipitation", 0),
                            "rain": current.get("rain", 0),
                            "weather_code": weather_code,
                            "weather_description": WeatherService._get_weather_description(
                                weather_code
                            ),
                            "emoji": WeatherService.get_weather_emoji(weather_code),
                            "cloud_cover": current.get("cloud_cover"),
                            "wind_speed": current.get("wind_speed_10m"),
                            "wind_direction": current.get("wind_direction_10m"),
                            "luminosity": luminosity,
                            "timestamp": current.get("time"),
                        }
            return None
        except Exception as e:
            print(f"Error getting weather: {e}")
            return None

    @staticmethod
    def _estimate_luminosity(cloud_cover: float, weather_code: int) -> float:
        """
        Estimer la luminosité en lux basée sur la couverture nuageuse.

        Args:
            cloud_cover: Pourcentage de couverture nuageuse (0-100)
            weather_code: Code météo WMO

        Returns:
            Luminosité estimée en lux
        """
        # Obtenir l'heure actuelle pour déterminer jour/nuit
        hour = datetime.now().hour

        # Nuit (18h-6h): faible luminosité
        if hour < 6 or hour >= 18:
            return 10.0  # Nuit: 10 lux (éclairage urbain)

        # Jour: calculer selon couverture nuageuse
        # Plein soleil: ~100,000 lux
        # Jour nuageux: ~10,000 lux
        # Très nuageux: ~1,000 lux

        base_lux = 100000  # Plein soleil

        # Réduction selon couverture nuageuse
        reduction_factor = 1 - (cloud_cover / 100)
        luminosity = base_lux * reduction_factor

        # Minimum 1000 lux pendant la journée même très nuageux
        luminosity = max(luminosity, 1000)

        # Réduction supplémentaire si pluie/orage
        if weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99]:
            luminosity *= 0.3

        return round(luminosity, 1)

    @staticmethod
    def _get_weather_description(code: int) -> str:
        """
        Obtenir la description météo en français depuis le code WMO.

        Args:
            code: Code météo WMO

        Returns:
            Description en français
        """
        weather_codes = {
            0: "Ciel dégagé",
            1: "Principalement dégagé",
            2: "Partiellement nuageux",
            3: "Couvert",
            45: "Brouillard",
            48: "Brouillard givrant",
            51: "Bruine légère",
            53: "Bruine modérée",
            55: "Bruine dense",
            61: "Pluie légère",
            63: "Pluie modérée",
            65: "Pluie forte",
            71: "Neige légère",
            73: "Neige modérée",
            75: "Neige forte",
            77: "Grains de neige",
            80: "Averses légères",
            81: "Averses modérées",
            82: "Averses violentes",
            85: "Averses de neige légères",
            86: "Averses de neige fortes",
            95: "Orage",
            96: "Orage avec grêle légère",
            99: "Orage avec grêle forte",
        }
        return weather_codes.get(code, "Inconnu")

    @staticmethod
    def get_weather_emoji(code: int) -> str:
        """
        Obtenir l'emoji correspondant au code météo.

        Args:
            code: Code météo WMO

        Returns:
            Emoji représentant la météo
        """
        if code == 0:
            return "☀️"
        elif code in [1, 2]:
            return "🌤️"
        elif code == 3:
            return "☁️"
        elif code in [45, 48]:
            return "🌫️"
        elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            return "🌧️"
        elif code in [71, 73, 75, 77, 85, 86]:
            return "🌨️"
        elif code in [95, 96, 99]:
            return "⛈️"
        return "🌍"
