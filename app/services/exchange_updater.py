import requests
from flask import current_app

from app import db
from app.models.bookmodel import ExchangeRate


SUPPORTED_CURRENCIES = [
    "EUR",
    "USD",
    "XOF",
    "XAF",
    "NGN",
    "GHS",
    "KES",
    "UGX",
    "RWF",
    "MAD",
    "ZAR",
    "JPY",
]

def update_exchange_rates():
    API_KEY = current_app.config["XCHANGE_RATE_API_KEY"]
    url = (
        f"https://v6.exchangerate-api.com/v6/"
        f"{API_KEY}/latest/GBP"
    )

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        data = response.json()
    except requests.RequestException as e:

        print("Exchange API connection failed")
        print(e)

        return False

    if data.get("result") != "success":

        print("Exchange API returned an error")
        print(data)

        return False

    rates = data["conversion_rates"]

    for currency in SUPPORTED_CURRENCIES:

        if currency == "GBP":
            continue

        rate = rates.get(currency)

        if rate is None:
            continue

        record = ExchangeRate.query.filter_by(base_currency="GBP",
                                              target_currency=currency
                                            ).first()

        if record:
            record.rate = rate

        else:
            db.session.add(ExchangeRate(base_currency="GBP",
                                        target_currency=currency,
                                        rate=rate
                                    )
                                )

    db.session.commit()

    print("Exchange rates updated successfully.")

    return True