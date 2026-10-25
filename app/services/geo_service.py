import os
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



def _clean_country(value):
    '''Two-letter ISO code only (upper-cased); anything else is ignored.'''
    value = (value or "").strip().upper()
    return value if len(value) == 2 and value.isalpha() else None


def detect_country():
    """
    Detect the visitor's country.
    Priority:
        1. Cloudflare header
        2. Reverse proxy header
        3. Development fallback
    """

    # Cloudflare (recommended in production)
    country = _clean_country(request.headers.get("CF-IPCountry"))

    if country:
        return country

    # Optional reverse proxy header. Any visitor can send this header
    # themselves, so it is only honoured when you explicitly say your
    # proxy sets/overwrites it (TRUST_COUNTRY_HEADER=1 in .env).
    if os.getenv("TRUST_COUNTRY_HEADER") == "1":
        country = _clean_country(request.headers.get("X-Country-Code"))

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