from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import AdminUser, Booking, Master, Service, Client, ServiceCategory
from datetime import datetime, date, timedelta
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)


# ─── Auth ────────────────────────────────────────────────────────────────────

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user     = AdminUser.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            return redirect(url_for('admin.dashboard'))
        flash('Неверный логин или пароль.', 'danger')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))


# ─── Dashboard ───────────────────────────────────────────────────────────────

@admin_bp.route('/')
@login_required
def dashboard():
    today     = date.today()
    tomorrow  = today + timedelta(days=1)

    today_bookings = Booking.query.filter(
        Booking.start_time >= datetime.combine(today,    datetime.min.time()),
        Booking.start_time <  datetime.combine(tomorrow, datetime.min.time()),
        Booking.status != 'cancelled',
    ).order_by(Booking.start_time).all()

    stats = {
        'today_count':   len(today_bookings),
        'pending_count': Booking.query.filter_by(status='pending').count(),
        'total_clients': Client.query.count(),
        'total_masters': Master.query.filter_by(is_active=True).count(),
    }

    return render_template('admin/dashboard.html',
                           today_bookings=today_bookings,
                           stats=stats,
                           today=today)


# ─── Bookings ────────────────────────────────────────────────────────────────

@admin_bp.route('/bookings')
@login_required
def bookings():
    status = request.args.get('status', '')
    query  = Booking.query.order_by(Booking.start_time.desc())
    if status:
        query = query.filter_by(status=status)
    all_bookings = query.limit(200).all()
    return render_template('admin/bookings.html', bookings=all_bookings, status=status)


@admin_bp.route('/bookings/<int:booking_id>/status', methods=['POST'])
@login_required
def update_booking_status(booking_id):
    booking    = Booking.query.get_or_404(booking_id)
    new_status = request.form.get('status')
    if new_status in ('pending', 'confirmed', 'completed', 'cancelled'):
        booking.status = new_status
        db.session.commit()
        flash(f'Статус записи #{booking_id} обновлён.', 'success')
    return redirect(url_for('admin.bookings'))


@admin_bp.route('/bookings/<int:booking_id>/delete', methods=['POST'])
@login_required
def delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    flash('Запись удалена.', 'success')
    return redirect(url_for('admin.bookings'))


# ─── Masters ─────────────────────────────────────────────────────────────────

@admin_bp.route('/masters')
@login_required
def masters():
    all_masters = Master.query.order_by(Master.name).all()
    return render_template('admin/masters.html', masters=all_masters)


@admin_bp.route('/masters/add', methods=['POST'])
@login_required
def add_master():
    master = Master(
        name      = request.form.get('name', '').strip(),
        specialty = request.form.get('specialty', '').strip(),
        bio       = request.form.get('bio', '').strip(),
        is_active = True,
    )
    db.session.add(master)
    db.session.commit()
    flash(f'Мастер {master.name} добавлен.', 'success')
    return redirect(url_for('admin.masters'))


@admin_bp.route('/masters/<int:master_id>/toggle', methods=['POST'])
@login_required
def toggle_master(master_id):
    master           = Master.query.get_or_404(master_id)
    master.is_active = not master.is_active
    db.session.commit()
    return redirect(url_for('admin.masters'))


@admin_bp.route('/masters/<int:master_id>/delete', methods=['POST'])
@login_required
def delete_master(master_id):
    master = Master.query.get_or_404(master_id)
    db.session.delete(master)
    db.session.commit()
    flash('Мастер удалён.', 'success')
    return redirect(url_for('admin.masters'))


# ─── Services ────────────────────────────────────────────────────────────────

@admin_bp.route('/services')
@login_required
def services():
    categories   = ServiceCategory.query.order_by(ServiceCategory.order).all()
    all_services = Service.query.order_by(Service.category_id, Service.title).all()
    return render_template('admin/services.html',
                           services=all_services,
                           categories=categories)


@admin_bp.route('/services/add', methods=['POST'])
@login_required
def add_service():
    service = Service(
        title            = request.form.get('title', '').strip(),
        description      = request.form.get('description', '').strip(),
        price            = float(request.form.get('price', 0)),
        duration_minutes = int(request.form.get('duration_minutes', 60)),
        category_id      = request.form.get('category_id') or None,
        is_active        = True,
    )
    db.session.add(service)
    db.session.commit()
    flash(f'Услуга «{service.title}» добавлена.', 'success')
    return redirect(url_for('admin.services'))


@admin_bp.route('/services/<int:service_id>/delete', methods=['POST'])
@login_required
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash('Услуга удалена.', 'success')
    return redirect(url_for('admin.services'))


# ─── Clients ─────────────────────────────────────────────────────────────────

@admin_bp.route('/clients')
@login_required
def clients():
    all_clients = Client.query.order_by(Client.created_at.desc()).all()
    return render_template('admin/clients.html', clients=all_clients)