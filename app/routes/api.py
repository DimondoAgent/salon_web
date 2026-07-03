from flask import Blueprint, jsonify, request
from app import db
from app.models import Service, Master, Booking, Client, ServiceCategory, MasterSchedule
from app.translations import t
from datetime import datetime, timedelta, date

api_bp = Blueprint('api', __name__)


@api_bp.route('/services')
def get_services():
    services = Service.query.filter_by(is_active=True).all()
    return jsonify([{
        'id':                s.id,
        'title':             s.title,
        'description':       s.description,
        'price':             float(s.price),
        'duration_minutes':  s.duration_minutes,
        'category_id':       s.category_id,
    } for s in services])


@api_bp.route('/masters')
def get_masters():
    masters = Master.query.filter_by(is_active=True).all()
    return jsonify([{
        'id':        m.id,
        'name':      m.name,
        'specialty': m.specialty,
        'photo_url': m.photo_url,
    } for m in masters])


@api_bp.route('/masters/<int:master_id>/slots')
def get_slots(master_id):
    """
    Returns available time slots for a master on a given date.
    Query params: date=YYYY-MM-DD, service_id=<int>
    """
    date_str   = request.args.get('date')
    service_id = request.args.get('service_id', type=int)

    if not date_str or not service_id:
        return jsonify({'error': 'date and service_id are required'}), 400

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    service = Service.query.get_or_404(service_id)
    master  = Master.query.get_or_404(master_id)

    # Check master's schedule for this weekday
    weekday  = target_date.weekday()   # 0=Mon
    schedule = MasterSchedule.query.filter_by(
        master_id=master_id, weekday=weekday
    ).first()

    if schedule and schedule.is_day_off:
        return jsonify([])

    # Default hours if no schedule set: 9–19
    start_hour = schedule.start_hour if schedule else 9
    end_hour   = schedule.end_hour   if schedule else 19

    # Fetch existing bookings for this master on this day
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end   = day_start + timedelta(days=1)

    existing = Booking.query.filter(
        Booking.master_id == master_id,
        Booking.start_time >= day_start,
        Booking.start_time < day_end,
        Booking.status != 'cancelled',
    ).all()

    # Build slots every 30 minutes
    slot_duration = timedelta(minutes=service.duration_minutes)
    slots = []
    current = datetime.combine(target_date, datetime.min.time()).replace(hour=start_hour)
    end     = datetime.combine(target_date, datetime.min.time()).replace(hour=end_hour)

    while current + slot_duration <= end:
        slot_end   = current + slot_duration
        overlapped = any(
            not (slot_end <= b.start_time or current >= b.end_time)
            for b in existing
        )
        if not overlapped:
            slots.append(current.strftime('%H:%M'))
        current += timedelta(minutes=30)

    return jsonify(slots)


@api_bp.route('/bookings', methods=['POST'])
def create_booking():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required = ('name', 'phone', 'master_id', 'service_id', 'date', 'time')
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Field {field} is required'}), 400

    try:
        start_time = datetime.strptime(f"{data['date']} {data['time']}", '%Y-%m-%d %H:%M')
    except ValueError:
        return jsonify({'error': 'Invalid date/time format'}), 400

    service = Service.query.get(data['service_id'])
    if not service:
        return jsonify({'error': 'Service not found'}), 404

    end_time = start_time + timedelta(minutes=service.duration_minutes)

    # Check slot is still free (race condition protection)
    overlap = Booking.query.filter(
        Booking.master_id == data['master_id'],
        Booking.status != 'cancelled',
        Booking.start_time < end_time,
        Booking.end_time > start_time,
    ).first()
    if overlap:
        return jsonify({'error': t('api.slot_taken')}), 409

    # Get or create client
    client = Client.query.filter_by(phone=data['phone']).first()
    if not client:
        client = Client(name=data['name'], phone=data['phone'], email=data.get('email'))
        db.session.add(client)
        db.session.flush()

    booking = Booking(
        client_id  = client.id,
        master_id  = data['master_id'],
        service_id = data['service_id'],
        start_time = start_time,
        end_time   = end_time,
        notes      = data.get('notes', ''),
        status     = 'pending',
    )
    db.session.add(booking)
    db.session.commit()

    # TODO: push to Google Calendar here
    # from app.services.google_calendar import create_event
    # event_id = create_event(booking)
    # booking.google_event_id = event_id
    # db.session.commit()

    return jsonify({
        'success':    True,
        'booking_id': booking.id,
        'message':    t('api.booking_created'),
    }), 201