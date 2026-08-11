from app.models.bookmodel import ExchangeRate

"""
Currency Service Handles:
    - Country → Currency
    - Currency symbols
    - Money formatting
"""

COUNTRY_CURRENCY = {
    "GB":"GBP",
    "FR":"EUR",
    "CI":"XOF",
    "SN":"XOF",
    "BF":"XOF",
    "ML":"XOF",
    "NE":"XOF",
    "TG":"XOF",
    "BJ":"XOF",
    "GW":"XOF",
    "CM":"XAF",
    "GA":"XAF",
    "CG":"XAF",
    "TD":"XAF",
    "CF":"XAF",
    "GQ":"XAF",
    "NG":"NGN",
    "GH":"GHS",
    "KE":"KES",
    "UG":"UGX",
    "RW":"RWF",
    "TZ":"TZS",
    "MA":"MAD",
    "EG":"EGP",
    "ZA":"ZAR",
    "US":"USD",
    "CA":"CAD",
    "JP":"JPY"
}

CURRENCY_SYMBOLS = {

    "GBP": "£",
    "EUR": "€",
    "USD": "$",
    "CAD": "C$",

    "XOF": "CFA",
    "XAF": "FCFA",

    "NGN": "₦",
    "GHS": "GH₵",
    "KES": "KSh",
    "UGX": "USh",
    "RWF": "RF",
    "TZS": "TSh",

    "MAD": "DH",
    "EGP": "E£",
    "TND": "DT",
    "JPY": "¥",

    "ZAR": "R",
}

def get_currency(country):
    """
    Return currency code for a country. Default is GBP.
    """
    return COUNTRY_CURRENCY.get(country, "GBP")

def get_symbol(currency):
    """
    Return currency symbol.
    """
    return CURRENCY_SYMBOLS.get(currency, currency)


def format_money(amount, currency="GBP"):
    if amount is None:
        amount = 0
    symbol = get_symbol(currency)
    return f"{symbol} {amount:,.2f}"


def get_exchange_rates():
    rates = {}
    rows = ExchangeRate.query.all()

    for row in rows:
        rates[row.target_currency] = row.rate
    rates["GBP"] = 1

    return rates


def convert(amount, target_currency):
    """
    Convert an amount from GBP to the target currency.
    """
    if target_currency == "GBP":
        return amount

    rate = ExchangeRate.query.filter_by(base_currency="GBP",
                                        target_currency=target_currency
                                        ).first()
    if not rate:
        return None

    return round(amount * rate.rate, 2)


def convert_currency(amount, from_currency, to_currency):

    if amount is None:
        return 0

    if from_currency == to_currency:
        return amount

    rates = get_exchange_rates()

    # Convert source currency to GBP
    if from_currency != "GBP":

        if from_currency not in rates:
            return amount
        
        amount = amount / rates[from_currency]
    # Convert GBP to destination currency
    if to_currency == "GBP":
        return round(amount, 2)
    
    if to_currency not in rates:
        return round(amount, 2)

    return round(amount * rates[to_currency], 2)


def format_converted(amount, currency):
    """
    Convert and format an amount using the room currency.
    """
    converted = convert(amount, currency)
    if converted is None:
        return ""
    symbol = get_symbol(currency)

    return f"{symbol} {converted:,.2f}"


def convert_and_format(amount, from_currency, to_currency):
    """
        Format converted money
    """
    converted = convert_currency(amount, from_currency, to_currency)

    return format_money(converted, to_currency)