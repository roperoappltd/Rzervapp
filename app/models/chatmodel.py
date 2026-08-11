from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin, current_user
from flask import current_app, render_template


class Conversation(db.Model):
    __tablename__ = "conversation"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), unique=True)
    guest_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    host_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    active = db.Column(db.Boolean, default=True)
    guest = db.relationship("User",foreign_keys=[guest_id])
    host = db.relationship("User", foreign_keys=[host_id])

    @property
    def other_user(self):
        if current_user.id == self.guest_id:
            return self.host
        return self.guest

    def __repr__(self):
        return f"Conversation('{self.active}')"

class Message(db.Model):
    __tablename__ = "message"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversation.id"))
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    body = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id", name='fk_message_rcver_id'))
    is_flagged = db.Column(db.Boolean,default=False)
    flag_reason = db.Column(db.String(255))

    def __repr__(self):
        return f"Message('{self.body}')"


# If you're using Gunicorn later:
# pip install eventlet
    