
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut

# Find longitude and latitude 
geolocator = Nominatim( user_agent="Jambo")
def get_location(city):
    """
        Finds the location of a room from the city entered by the host.
    """
    # Prevent invalid lookups
    if not city:
        return None

    city = city.strip()

    if city == "":
        return None

    try:
        location = geolocator.geocode(city, language="en", timeout=10)

        if not location:
            return None

        address = location.raw.get("display_name")
        address_data = location.raw.get("address", {})

        return {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "city": (
                address_data.get("city")
                or address_data.get("town")
                or address_data.get("village")
            ),
            "country": address_data.get("country"),
            "full_address": address,
        }

    except (GeocoderUnavailable, GeocoderTimedOut):
        return None