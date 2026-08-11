
from app.models.bookmodel import Bookings
from app.models.usermodel import User
from app.models.roommodel import Rooms

def get_dashboard_stats():
    return {
        "total_users": User.query.count(),
        "total_rooms": Rooms.query.count(),
        "total_bookings": Bookings.query.count(),
        "total_revenue": 0,
        "earnings_state": 50
    }