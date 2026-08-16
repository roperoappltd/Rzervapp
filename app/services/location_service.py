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
            # FIXED: COUNTRY_CURRENCY's keys are 2-letter ISO codes
            # ("CI", "GB", "FR"), but the "country" field above is the
            # FULL country name ("Côte d'Ivoire") -- looking that up
            # directly against COUNTRY_CURRENCY has been silently
            # failing for every single room ever created, always
            # falling back to the "GBP" default regardless of the
            # room's actual country. country_code is the correct field
            # for that lookup; "country" stays as-is since room_country
            # (a human-readable display field) correctly wants the full name.
            "country_code": (address_data.get("country_code") or "").upper(),
            "full_address": address,
        }

    except (GeocoderUnavailable, GeocoderTimedOut):
        return None