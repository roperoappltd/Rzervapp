from datetime import date, timedelta
from app.models.roommodel import RoomView
from app import db
from sqlalchemy import func


def get_daily_view_counts(room_id, days):
    '''
    Returns a list of {"date": "12 Jul", "count": N} covering the last
    `days` days, oldest first, INCLUDING days with zero views.
 
    Why the zero-fill matters: a plain GROUP BY only returns rows for
    days that actually had a view -- a room with no views on, say, three
    of the last seven days would silently have those days missing from
    the result entirely, not present-with-0. Charted directly, that
    produces a misleading line (points connect across the gap instead of
    dipping to zero) rather than an honest flat/empty period.
    '''
    start_date = date.today() - timedelta(days=days - 1)
 
    rows = (
        db.session.query(
            func.date(RoomView.viewed_at).label('day'),
            func.count(RoomView.id).label('cnt'),
        )
        .filter(RoomView.room_id == room_id, RoomView.viewed_at >= start_date)
        .group_by(func.date(RoomView.viewed_at))
        .all()
    )
    counts_by_day = {str(r.day): r.cnt for r in rows}
 
    result = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        result.append({
            "date": d.strftime('%d %b'),
            "count": counts_by_day.get(str(d), 0),
        })
    return result
 