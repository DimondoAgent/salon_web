from flask import Blueprint, render_template
from app.models import Service, ServiceCategory, Master, Booking

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    categories = ServiceCategory.query.order_by(ServiceCategory.order).all()
    masters    = Master.query.filter_by(is_active=True).all()
    return render_template('index.html', categories=categories, masters=masters)


@main_bp.route('/services')
def services():
    categories = ServiceCategory.query.order_by(ServiceCategory.order).all()
    return render_template('services.html', categories=categories)


@main_bp.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')


@main_bp.route('/booking')
def booking():
    services   = Service.query.filter_by(is_active=True).order_by(Service.category_id).all()
    masters    = Master.query.filter_by(is_active=True).all()
    categories = ServiceCategory.query.order_by(ServiceCategory.order).all()
    return render_template('booking.html',
                           services=services,
                           masters=masters,
                           categories=categories)


@main_bp.route('/contacts')
def contacts():
    return render_template('contacts.html')