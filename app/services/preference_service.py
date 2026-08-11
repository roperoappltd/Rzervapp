from flask import session
from flask_login import current_user
from app.services.geo_service import (detect_country, detect_language)
from app.services.currency import (COUNTRY_CURRENCY)


class VisitorPreferences:

    def __init__(self):
        # country
        self.country = detect_country()

        # Language
        if "language" not in session:
            session["language"] = detect_language()

        self.language = session["language"]

        # Currency
        if "currency" not in session:
            if (current_user.is_authenticated and current_user.preferred_currency):
                session["currency"] = (current_user.preferred_currency)

            else:
                session["currency"] = COUNTRY_CURRENCY.get(self.country, "GBP")

        self.currency = session["currency"]