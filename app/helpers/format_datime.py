from datetime import datetime

# date formatter
def format_message_time(dt):
    now = datetime.utcnow().date()
    if dt.date() == now:
        return dt.strftime("%H:%M")
    elif (now - dt.date()).days == 1:
        return "Yesterday " + dt.strftime("%H:%M")
    else:
        return dt.strftime("%d %b %Y, %H:%M")