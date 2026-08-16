from flask_admin import AdminIndexView, expose
from app.services.admin_dashboard import get_dashboard_stats
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import abort, render_template
from app import db, admin
from app.services.auth import role_required
from app.models.usermodel import User
from app.models.bookmodel import Bookings, Payments
from app.models.roommodel import Rooms
from app.models.chatmodel import Conversation


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        stats = get_dashboard_stats()

        return self.render("adminpanel/admindash.html", **stats)

# Pass the custom view to the Admin instance
# admin = Admin(app, index_view=MyAdminIndexView())

class UserAdmin(ModelView):
    # Columns displayed
    column_list = ("id", "username", "email", "is_admin", "email_verified",
                   "failed_login_attempts", "locked_until", "created_at")  # FIXED: removed 'role' (deleted from User); added lockout visibility
    # Search
    column_searchable_list = ("username", "email")
    # Filters
    column_filters = ("is_admin", "email_verified", "created_at")  # FIXED: removed 'role'
    # Sorting
    column_sortable_list = ("id", "username", "email", "created_at")
    # Quick inline edit -- lets an admin clear a lockout with one click,
    # right from the list view, without opening the full edit form.
    column_editable_list = ("failed_login_attempts", "locked_until", "is_admin", "email_verified")

    # SECURITY: explicit whitelist, not an exclude-list. Anything not
    # listed here (password, in particular) never appears on the admin
    # edit form at all -- a new sensitive field added to User later is
    # safe by default, rather than needing someone to remember to exclude
    # it. Never list `password` here -- Flask-Admin has no concept of
    # bcrypt hashing, so an edited value would be saved as plain text,
    # silently breaking that user's login.
    form_columns = ("first_name", "last_name", "gender", "dob",
                     "address", "city", "zip_code", "country",
                     "company_name", "phone", "username", "email",
                     "is_admin", "email_verified", "aboutme",
                     "rzerv_points", "language", "preferred_currency",
                     "failed_login_attempts", "locked_until")

    # Column formatter 
    column_formatters = {   "is_admin": lambda v, c, m, p:
                                "👑 Admin" if m.is_admin else "👨🏻‍💼 User",

                            "created_at": lambda v, c, m, p:
                                m.created_at.strftime("%d-%m-%Y %H:%M")
                                if m.created_at else ""
                        }
    # Pagination
    page_size = 8

    def is_accessible(self):  # FIXED: removed @role_required('admin') -- likely referenced the deleted `role` field, and was redundant with this body anyway
        return (
            current_user.is_authenticated
            and current_user.is_admin
        )

    def inaccessible_callback(self, name, **kwargs):  # FIXED: was named not_auth -- Flask-Admin never calls a method by that name, so the custom 403 template was silently never used
        return render_template('errors/403.html'), 403
    
    #def inaccessible_callback(self, name, **kwargs):
    #    abort(403)

class RoomAdmin(ModelView):
    # Columns displayed
    column_list = ("id", "room_name", "price", "room_currency", "room_country", "status", "created_at")  # FIXED: 'currency' -> 'room_currency'; added 'status', useful at a glance

    # Search -- text fields only
    column_searchable_list = ("room_name", "room_country", "room_location", "borough")  # FIXED: removed 'price' -- LIKE against a Numeric column works by accident on SQLite, likely breaks on MySQL

    # Filters -- price belongs here (range/exact match), not in text search
    column_filters = ("room_country", "room_category", "status", "price", "room_currency")

    column_labels = dict(room_country='Country', created_at='Added on', room_currency='Currency')

    # Sorting
    column_sortable_list = ("id", "price", "created_at")

    # Column formatting 
    column_formatters = {"created_at": lambda v, c, m, p:
                            m.created_at.strftime("%d-%m-%Y %H:%M")
                            if m.created_at else ""
                        }

    # Explicit whitelist -- lower stakes than User (nothing as sensitive
    # as a password here), but still worth being deliberate about which
    # fields an admin can edit directly, e.g. leaving room ownership
    # (user_id) reassignment as an intentional inclusion, not an accident
    # of an unset default.
    form_columns = ("room_name", "room_location", "borough", "room_country", "room_category",
                     "price", "room_currency", "max_occupancy", "room_size",
                     "short_desc", "description", "status",
                     "rule1", "rule2", "rule3",
                     "image1", "image2", "image3", "image4", "image5", "image6",
                     "user_id")

    # Pagination
    page_size = 8

    def is_accessible(self):  # role_required decorator removed -- redundant with this body, and no longer needed now that role_required itself is fixed at its source
        return (
            current_user.is_authenticated
            and current_user.is_admin
        )
    def inaccessible_callback(self, name, **kwargs): 
        return render_template('errors/403.html'), 403

class BookAdmin(ModelView):
    # Columns displayed
    column_list = ("id", "booking_num", "arrival", "departure", "primary_guest",
                   "pguest_email", "status", "active", "created_at")
    # Search -- text fields only
    column_searchable_list = ("pguest_email", "primary_guest", "booking_num")  # FIXED: removed 'arrival' (Date column)
    # Filters -- date belongs here, not in text search
    column_filters = ("arrival", "departure", "status", "active", "created_at")
    # Sorting
    column_sortable_list = ("id", "primary_guest", "pguest_email", "created_at")

    # Column formatter
    column_formatters = {
                        # NEUTRALIZED pending real status values -- the
                        # original checked for "Confirmed"/"Cancel" but
                        # Bookings.status defaults to 'Pending', which
                        # isn't handled and would fall through to
                        # "Expired", mislabeling every new booking. Shows
                        # the raw value until the real lifecycle is
                        # confirmed.
                        "status": lambda v, c, m, p: m.status,

                        "created_at": lambda v, c, m, p:
                            m.created_at.strftime("%d-%m-%Y %H:%M")
                            if m.created_at else ""
                        }

    # Maximally restrictive whitelist: dates, financial fields
    # (serv_charge*), and foreign keys (room_id/user_id/deal_id) are
    # view-only via column_list, never editable here. Changing dates or
    # financials by hand would desync them from what create_booking()
    # actually calculated and charged. Only what a support admin
    # genuinely needs to correct or moderate is included.
    form_columns = ("primary_guest", "pguest_email", "pguest_phone",
                     "ad_info", "status", "active")

    # Pagination
    page_size = 8

    def is_accessible(self):  # role_required decorator removed -- returns a tuple on rejection, which is always truthy, silently inverting the access check
        return (
            current_user.is_authenticated
            and current_user.is_admin
        )
    def inaccessible_callback(self, name, **kwargs):  
        return render_template('errors/403.html'), 403

class PayAdmin(ModelView):
    # Columns displayed
    column_list = ("id", "payment_date", "pay_method", "accounting_amount", "payment_currency",
                   "transac_fee_host", "status")  # FIXED: 'transac_fee' -> 'transac_fee_host'

    # Search -- text fields only, including a lookup by booking reference
    column_searchable_list = ("pay_method", "payment_currency", "booking.booking_num")  # FIXED: removed payment_date/total_paid (Date/Numeric columns); added booking_num lookup

    # Filters -- date/amount/status belong here, not in text search
    column_filters = ("payment_date", "status", "pay_method", "payment_currency", "accounting_amount")

    column_labels = dict(
        payment_date='Payment Date',
        pay_method='Method',
        accounting_amount='Total Paid',
        payment_currency='Currency',
        transac_fee_host="Transac. Fee (Host Currency)",
    )

    # Sorting
    column_sortable_list = ("id", "accounting_amount", "payment_date")

    # Column formatting 
    column_formatters = {"payment_date": lambda v, c, m, p:
                            m.payment_date.strftime("%d-%m-%Y %H:%M")
                            if m.payment_date else ""
                        }

    # Tightened per the same reasoning as BookAdmin -- every calculated
    # financial field (room_price_gbp, total_paid, accounting_amount,
    # both exchange rates, both currency codes) is view-only. Only what
    # an admin needs to correct/manage for support purposes is editable.
    form_columns = ("status", "pay_method")

    # Pagination
    page_size = 8

    def is_accessible(self):
        return (
            current_user.is_authenticated
            and current_user.is_admin
        )
    def inaccessible_callback(self, name, **kwargs):  
        return render_template('errors/403.html'), 403

# ==============================================================================
# Propagating the views
admin.add_view(UserAdmin(User, db.session, name="Users"))
admin.add_view(RoomAdmin(Rooms, db.session, name="Rooms"))
admin.add_view(BookAdmin(Bookings, db.session, name="Bookings"))
admin.add_view(PayAdmin(Payments, db.session, name="Payments"))