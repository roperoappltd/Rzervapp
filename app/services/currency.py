from app.models.bookmodel import ExchangeRate
from decimal import Decimal

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


# Currencies with no minor unit actually used in practice, confirmed
# against ISO 4217's official "exponent 0" list -- e.g. XOF's centime is
# described by name as "theoretical (unused)". Limited to currencies
# this app actually supports; the full ISO list is longer.
ZERO_DECIMAL_CURRENCIES = {"XOF", "XAF", "UGX", "RWF", "JPY"}

def format_money(amount, currency="GBP"):
    if amount is None:
        amount = 0
    symbol = get_symbol(currency)
    if currency in ZERO_DECIMAL_CURRENCIES:
        return f"{symbol} {amount:,.0f}"
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

    # Same Decimal/float mixing fix as convert_currency() above.
    return float(round(Decimal(str(amount)) * Decimal(str(rate.rate)), 2))


def convert_currency(amount, from_currency, to_currency):

    if amount is None:
        return 0

    if from_currency == to_currency:
        return amount

    # Normalize to Decimal for the arithmetic -- ExchangeRate.rate is a
    # Numeric column, which SQLAlchemy returns as Decimal by default.
    # Mixing that directly against a plain float `amount` throws:
    # TypeError: unsupported operand type(s) for /: 'float' and
    # 'decimal.Decimal'. Converting via str() (never float(Decimal)
    # directly, which can introduce tiny binary floating-point rounding
    # error) keeps both sides consistently Decimal through the math.
    # Cast back to float at the very end, so this function's return
    # type stays exactly what every existing caller already expects --
    # this fix is scoped to the internal arithmetic only.
    amount = Decimal(str(amount))

    rates = get_exchange_rates()

    # Convert source currency to GBP
    if from_currency != "GBP":

        if from_currency not in rates:
            return float(amount)
        
        amount = amount / Decimal(str(rates[from_currency]))
    # Convert GBP to destination currency
    if to_currency == "GBP":
        return float(round(amount, 2))
    
    if to_currency not in rates:
        return float(round(amount, 2))

    return float(round(amount * Decimal(str(rates[to_currency])), 2))


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


def format_room_price(room):
    '''
    Converts a Rooms' price (stored in room.room_currency) into the
    current viewer's detected/preferred currency and returns a
    formatted display string (e.g. "€142.50"). Centralizes this so
    every template showing a room's price gets it consistently --
    found several different broken/inconsistent approaches scattered
    across templates: a hardcoded £ regardless of the room's actual
    currency, a reference to a nonexistent room.currency attribute
    (the real field is room_currency), and raw price with no currency
    indicator at all.
    '''
    from app.services.preference_service import VisitorPreferences  # local import -- avoids a circular import, since preference_service already imports FROM this module at its own top level
    guest_currency = VisitorPreferences().currency
    return convert_and_format(float(room.price), room.room_currency, guest_currency)