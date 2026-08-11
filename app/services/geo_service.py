from flask import request

COUNTRY_LANGUAGE = {
    # English-speaking
    "GB": "en",
    "US": "en",
    "CA": "en",
    "GH": "en",
    "NG": "en",
    "KE": "en",
    "UG": "en",
    "TZ": "en",
    "RW": "en",
    "ZA": "en",

    # French-speaking
    "FR": "fr",
    "CI": "fr",
    "SN": "fr",
    "BF": "fr",
    "ML": "fr",
    "NE": "fr",
    "BJ": "fr",
    "TG": "fr",
    "CM": "fr",
    "GA": "fr",
    "CG": "fr",
    "CF": "fr",
    "TD": "fr",
    "GQ": "fr",
    "MA": "fr",
}



def detect_country():
    """
    Detect the visitor's country.
    Priority:
        1. Cloudflare header
        2. Reverse proxy header
        3. Development fallback
    """

    # Cloudflare (recommended in production)
    country = request.headers.get("CF-IPCountry")

    if country:
        return country

    # Optional reverse proxy header
    country = request.headers.get("X-Country-Code")

    if country:
        return country

    # Local development

    return "GB"

def detect_language():
    """
        Return the default language for the visitor.
    """
    country = detect_country()

    return COUNTRY_LANGUAGE.get(country, "en")