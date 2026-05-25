from datetime import * 
import secrets
room_location = [('Abidjan',), ('Watford,',), ('London',), ('Paris',), ('Nairobi',)]

def days_between(d1, d2):
    a = datetime.datetime.strptime(str(d1), "%Y-%m-%d").date()
    b = datetime.datetime.strptime(str(d2), "%Y-%m-%d").date()
    res = b - a
    return int(res.days)

#choices = [city for city in room_location]

#print(choices[1])

def number_generator():
    # create a random hex of 4 bytes
    random_hex = secrets.token_hex(3)
    a = 'BRZ06'
    booking_number = f'{a}'+ random_hex
    return booking_number

#print(number_generator())

def add_aday(d1, days):
    tomorrow = d1 + timedelta(days=days)
    return tomorrow

current_date = date.today()

#print(add_aday(current_date, 1))
def fee_calculator(bill, percentage=10, divider=100):
    trasaction_fee = (bill * percentage ) / divider
    return trasaction_fee

print(fee_calculator(200))
