from app import db, login_manager
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# ─── Auth ────────────────────────────────────────────────────────────────────

class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))


# ─── Core entities ───────────────────────────────────────────────────────────

class Client(db.Model):
    __tablename__ = 'clients'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    phone      = db.Column(db.String(20), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship('Booking', backref='client', lazy='dynamic')

    def __repr__(self):
        return f'<Client {self.name}>'


class Master(db.Model):
    __tablename__ = 'masters'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    specialty   = db.Column(db.String(150), nullable=False)
    bio         = db.Column(db.Text, nullable=True)
    photo_url   = db.Column(db.String(255), nullable=True)  # path to uploaded photo
    is_active   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    bookings     = db.relationship('Booking', backref='master', lazy='dynamic')
    work_hours   = db.relationship('MasterSchedule', backref='master', lazy='dynamic')

    def __repr__(self):
        return f'<Master {self.name}>'


class ServiceCategory(db.Model):
    __tablename__ = 'service_categories'

    id    = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(100), nullable=False)
    icon  = db.Column(db.String(50), nullable=True)   # emoji or icon name
    order = db.Column(db.Integer, default=0)

    services = db.relationship('Service', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class Service(db.Model):
    __tablename__ = 'services'

    id                = db.Column(db.Integer, primary_key=True)
    category_id       = db.Column(db.Integer, db.ForeignKey('service_categories.id'), nullable=True)
    title             = db.Column(db.String(150), nullable=False)
    description       = db.Column(db.Text, nullable=True)
    price             = db.Column(db.Numeric(10, 2), nullable=False)
    duration_minutes  = db.Column(db.Integer, nullable=False)  # critical for slot logic & Google Cal
    is_active         = db.Column(db.Boolean, default=True)

    bookings = db.relationship('Booking', backref='service', lazy='dynamic')

    def __repr__(self):
        return f'<Service {self.title}>'


class Booking(db.Model):
    __tablename__ = 'bookings'

    id         = db.Column(db.Integer, primary_key=True)
    client_id  = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    master_id  = db.Column(db.Integer, db.ForeignKey('masters.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)

    start_time = db.Column(db.DateTime, nullable=False)
    end_time   = db.Column(db.DateTime, nullable=False)

    # pending → confirmed → completed | cancelled
    status     = db.Column(db.String(20), default='pending', nullable=False)
    notes      = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Google Calendar integration — filled after event is pushed to GCal
    google_event_id = db.Column(db.String(255), nullable=True, unique=True)

    def __repr__(self):
        return f'<Booking {self.start_time} master={self.master_id} status={self.status}>'


class MasterSchedule(db.Model):
    """Working hours for each master per weekday (0=Mon … 6=Sun)."""
    __tablename__ = 'master_schedules'

    id         = db.Column(db.Integer, primary_key=True)
    master_id  = db.Column(db.Integer, db.ForeignKey('masters.id'), nullable=False)
    weekday    = db.Column(db.Integer, nullable=False)   # 0–6
    start_hour = db.Column(db.Integer, default=9)        # 9 = 09:00
    end_hour   = db.Column(db.Integer, default=19)       # 19 = 19:00
    is_day_off = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Schedule master={self.master_id} day={self.weekday}>'