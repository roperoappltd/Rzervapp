from app.models.bookmodel import ExchangeRate

def convert_amount(amount, currency):
    rate = ExchangeRate.query.filter_by(base_currency="GBP",
                                        target_currency=currency).first()

    if not rate:
        return amount
    return round(amount * rate.rate, 2)