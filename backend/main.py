from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import redis
from flask_cors import CORS 
import os

app = Flask(__name__)

CORS(app, 
     origins=["http://localhost:5173", "http://127.0.0.1:5173"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)


# === Configuration ===
app.config.update(
    SECRET_KEY='your-secret-key-here',
    SQLALCHEMY_DATABASE_URI='sqlite:///parking_app.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    JWT_SECRET_KEY='jwt-secret-string',
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=24),
)


# Initialize the Celery app
from celery_app import celery_app


# === Extensions ===
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


# === Models ===
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reservations = db.relationship('Reservation', backref='user', lazy=True)

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    address = db.Column(db.Text, nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    number_of_spots = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    spots = db.relationship('ParkingSpot', backref='lot', lazy=True, cascade='all, delete-orphan')

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(1), default='A')  # A-Available, O-Occupied
    reservations = db.relationship('Reservation', backref='spot', lazy=True, cascade='all, delete-orphan')

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    leaving_timestamp = db.Column(db.DateTime)
    parking_cost = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')
    vehicle_number = db.Column(db.String(20))
    base_cost = db.Column(db.Float, default=0.0)
    hourly_rate = db.Column(db.Float, default=0.0)
    total_hours = db.Column(db.Float, default=0.0)
    cost_breakdown = db.Column(db.Text)


# === Utilities ===
def init_admin():
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username='admin',
            email='admin@parking.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()

def calculate_parking_cost(reservation, lot_price, leaving_time=None):
    """Calculate detailed parking cost breakdown"""
    if leaving_time is None:
        leaving_time = datetime.utcnow()
    
    duration_hours = (leaving_time - reservation.parking_timestamp).total_seconds() / 3600
    
    base_hours = 1.0
    base_cost = lot_price * base_hours
    
    additional_hours = max(0, duration_hours - base_hours)
    additional_cost = additional_hours * lot_price
    
    total_cost = base_cost + additional_cost
    
    breakdown = {
        'base_cost': round(base_cost, 2),
        'hourly_rate': lot_price,
        'total_hours': round(duration_hours, 2),
        'additional_hours': round(additional_hours, 2),
        'additional_cost': round(additional_cost, 2),
        'total_cost': round(total_cost, 2),
        'calculation_time': leaving_time.isoformat()
    }
    
    return breakdown

def get_cache_key(prefix, *args):
    return f"{prefix}:{'_'.join(map(str, args))}"

def cache_get(key):
    try:
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except:
        return None

def cache_set(key, data, expire=300):
    try:
        redis_client.setex(key, expire, json.dumps(data))
    except:
        pass

def migrate_existing_reservations():
    """Migrate existing reservations to include cost breakdown"""
    try:
        db.session.execute(db.text("SELECT base_cost FROM reservation LIMIT 1"))
        reservations = Reservation.query.filter(Reservation.cost_breakdown.is_(None)).all()
    except Exception:
        print("New columns not found in database. Skipping migration - will run after first restart.")
        return
    
    for res in reservations:
        if res.hourly_rate is None or res.hourly_rate == 0:
            lot_price = res.spot.lot.price
            res.hourly_rate = lot_price
            res.base_cost = lot_price
            
            if res.leaving_timestamp:
                breakdown = calculate_parking_cost(res, lot_price, res.leaving_timestamp)
                res.total_hours = breakdown['total_hours']
                res.cost_breakdown = json.dumps(breakdown)
                res.parking_cost = breakdown['total_cost']
            else:
                res.total_hours = 1.0
                breakdown = {
                    'base_cost': lot_price,
                    'hourly_rate': lot_price,
                    'total_hours': 1.0,
                    'additional_hours': 0,
                    'additional_cost': 0,
                    'total_cost': lot_price
                }
                res.cost_breakdown = json.dumps(breakdown)
                res.parking_cost = lot_price
    
    db.session.commit()
    print(f"Migrated {len(reservations)} reservations with cost breakdown")

# === Routes ===
@app.route('/')
def root():
    return jsonify({"status": "Backend is running"})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first() or User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 400

    user = User(
        username=data['username'],
        email=data['email'],
        phone=data.get('phone', ''),
        password_hash=generate_password_hash(data['password'])
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        token = create_access_token(identity=str(user.id))
        return jsonify({
            'access_token': token,
            'user': { 'id': user.id, 'username': user.username, 'email': user.email, 'role': user.role }
        }), 200
    return jsonify({'message': 'Invalid credentials'}), 401


# === ADMIN ROUTES ===
@app.route('/api/admin/dashboard', methods=['GET'])
@jwt_required()
def admin_dashboard():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    total_lots = ParkingLot.query.count()
    total_spots = ParkingSpot.query.count()
    occupied_spots = ParkingSpot.query.filter_by(status='O').count()
    total_users = User.query.filter_by(role='user').count()
    active_reservations = Reservation.query.filter_by(status='active').count()
    
    return jsonify({
        'total_lots': total_lots,
        'total_spots': total_spots,
        'occupied_spots': occupied_spots,
        'available_spots': total_spots - occupied_spots,
        'total_users': total_users,
        'active_reservations': active_reservations
    })

@app.route('/api/parking-lots', methods=['POST'])
@jwt_required()
def create_parking_lot():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    data = request.get_json()
    
    lot = ParkingLot(
        prime_location_name=data['prime_location_name'],
        price=data['price'],
        address=data['address'],
        pin_code=data['pin_code'],
        number_of_spots=data['number_of_spots']
    )
    
    db.session.add(lot)
    db.session.flush()
    
    for i in range(1, data['number_of_spots'] + 1):
        spot = ParkingSpot(lot_id=lot.id, spot_number=i)
        db.session.add(spot)
    
    db.session.commit()
    
    redis_client.delete(get_cache_key('parking_lots'))
    
    return jsonify({'message': 'Parking lot created successfully'}), 201

@app.route('/api/parking-lots/<int:lot_id>', methods=['PUT'])
@jwt_required()
def update_parking_lot(lot_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    lot = ParkingLot.query.get_or_404(lot_id)
    data = request.get_json()
    
    lot.prime_location_name = data['prime_location_name']
    lot.price = data['price']
    lot.address = data['address']
    lot.pin_code = data['pin_code']
    
    new_spot_count = data['number_of_spots']
    current_spot_count = lot.number_of_spots
    
    if new_spot_count > current_spot_count:
        for i in range(current_spot_count + 1, new_spot_count + 1):
            spot = ParkingSpot(lot_id=lot.id, spot_number=i)
            db.session.add(spot)
    elif new_spot_count < current_spot_count:
        spots_to_remove = ParkingSpot.query.filter_by(lot_id=lot.id).filter(
            ParkingSpot.spot_number > new_spot_count
        ).all()
        
        for spot in spots_to_remove:
            if spot.status == 'O':
                return jsonify({'message': 'Cannot reduce spots with occupied spaces'}), 400
            db.session.delete(spot)
    
    lot.number_of_spots = new_spot_count
    db.session.commit()
    
    redis_client.delete(get_cache_key('parking_lots'))
    
    return jsonify({'message': 'Parking lot updated successfully'})

@app.route('/api/parking-lots/<int:lot_id>', methods=['DELETE'])
@jwt_required()
def delete_parking_lot(lot_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    lot = ParkingLot.query.get_or_404(lot_id)
    
    occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
    if occupied_spots > 0:
        return jsonify({'message': 'Cannot delete lot with occupied spots'}), 400
    
    for spot in lot.spots:
        Reservation.query.filter_by(spot_id=spot.id).delete()

    ParkingSpot.query.filter_by(lot_id=lot.id).delete()

    db.session.delete(lot)
    db.session.commit()
    
    redis_client.delete(get_cache_key('parking_lots'))
    
    return jsonify({'message': 'Parking lot deleted successfully'})

@app.route('/api/all-reservations', methods=['GET'])
@jwt_required()
def get_all_reservations():
    current_user = get_jwt_identity()
    user = User.query.get(current_user)
    if user.role != 'admin':
        return jsonify({'msg': 'Unauthorized'}), 403

    reservations = Reservation.query.order_by(Reservation.parking_timestamp.desc()).all()

    data = []
    for res in reservations:
        if res.cost_breakdown:
            breakdown = json.loads(res.cost_breakdown)
        else:
            breakdown = {
                'total_cost': res.parking_cost or 0,
                'hourly_rate': res.hourly_rate or 0,
                'total_hours': res.total_hours or 0
            }

        if res.status == 'active':
            current_breakdown = calculate_parking_cost(res, res.hourly_rate)
            breakdown.update(current_breakdown)
        
        data.append({
            'id': res.id,
            'username': res.user.username,
            'lot': res.spot.lot.prime_location_name,
            'spot_number': res.spot.spot_number,
            'vehicle_number': res.vehicle_number,
            'parking_timestamp': res.parking_timestamp.isoformat(),
            'leaving_timestamp': res.leaving_timestamp.isoformat() if res.leaving_timestamp else None,
            'parking_cost': res.parking_cost,
            'status': res.status,
            'cost_breakdown': breakdown
        })

    return jsonify(data), 200

@app.route('/api/reservations/<int:lot_id>', methods=['GET'])
@jwt_required()
def get_reservations_by_lot(lot_id):
    current_user = get_jwt_identity()
    user = User.query.get(current_user)
    if user.role != 'admin':
        return jsonify({'msg': 'Unauthorized'}), 403

    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    summary = []
    details = []

    for spot in spots:
        summary.append({
            'spot_number': spot.spot_number,
            'status': spot.status  # 'O' or 'A'
        })

        if spot.status == 'O':
            res = Reservation.query.filter_by(spot_id=spot.id, status='active').order_by(Reservation.parking_timestamp.desc()).first()
            if res:
                details.append({
                    'username': res.user.username,
                    'spot_number': spot.spot_number,
                    'vehicle_number': res.vehicle_number,
                    'parking_timestamp': res.parking_timestamp.isoformat(),
                    'leaving_timestamp': res.leaving_timestamp.isoformat() if res.leaving_timestamp else None,
                    'status': 'Occupied'
                })

    return jsonify({
        'lot_id': lot_id,
        'total_spots': len(spots),
        'occupied_count': sum(1 for s in summary if s['status'] == 'O'),
        'summary': summary,
        'details': details
    }), 200

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def get_all_users():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    users = User.query.filter_by(role='user').all()
    users_data = []
    
    for u in users:
        users_data.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'phone': u.phone,
            'created_at': u.created_at.isoformat(),
            'total_reservations': len(u.reservations)
        })
    
    return jsonify(users_data)


@app.route('/api/admin/statistics', methods=['GET'])
@jwt_required()
def admin_statistics():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        
        from sqlalchemy import func, extract
        from datetime import datetime, timedelta
        
        six_months_ago = datetime.now() - timedelta(days=180)
        
        # Revenue by month - only get completed reservations with cost
        revenue_data = db.session.query(
            extract('month', Reservation.leaving_timestamp).label('month'),
            extract('year', Reservation.leaving_timestamp).label('year'),
            func.sum(Reservation.parking_cost).label('total_revenue')
        ).filter(
            Reservation.leaving_timestamp >= six_months_ago,
            Reservation.status.in_(['completed', 'parked out']),
            Reservation.parking_cost.isnot(None)
        ).group_by(
            extract('year', Reservation.leaving_timestamp),
            extract('month', Reservation.leaving_timestamp)
        ).order_by(
            extract('year', Reservation.leaving_timestamp),
            extract('month', Reservation.leaving_timestamp)
        ).all()
        
        months = []
        revenue = []
        
        if not revenue_data:
            # Provide sample months if no data
            current_date = datetime.now()
            for i in range(6):
                month_date = current_date - timedelta(days=30*i)
                months.insert(0, month_date.strftime('%B %Y'))
                revenue.insert(0, 0)
        else:
            for row in revenue_data:
                month_num = int(row.month)
                year_num = int(row.year)
                
                date_obj = datetime(year_num, month_num, 1)
                month_str = date_obj.strftime('%B %Y')
                
                months.append(month_str)
                revenue.append(float(row.total_revenue or 0))
        
        # Parking lot utilization
        lots = ParkingLot.query.all()
        lot_names = []
        utilization_rates = []
        
        if not lots:
            lot_names = ['No Lots Available']
            utilization_rates = [0]
        else:
            for lot in lots:
                total_spots = lot.number_of_spots
                occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
                utilization = (occupied_spots / total_spots * 100) if total_spots > 0 else 0
                
                lot_names.append(lot.prime_location_name)
                utilization_rates.append(round(utilization, 1))
        
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        daily_reservations = db.session.query(
            func.date(Reservation.parking_timestamp).label('date'),
            func.count(Reservation.id).label('count')
        ).filter(
            Reservation.parking_timestamp >= seven_days_ago
        ).group_by(
            func.date(Reservation.parking_timestamp)
        ).order_by('date').all()
        
        reservation_dict = {}
        for row in daily_reservations:
            try:
                if hasattr(row.date, 'strftime'):
                    date_str = row.date.strftime('%m/%d')
                else:
                    from datetime import datetime
                    parsed_date = datetime.strptime(str(row.date), '%Y-%m-%d')
                    date_str = parsed_date.strftime('%m/%d')
                reservation_dict[date_str] = row.count
            except Exception as e:
                print(f"Error processing date {row.date}: {e}")
                continue
        
        days = []
        reservation_counts = []
        
        for i in range(7):
            day_date = datetime.now() - timedelta(days=6-i)
            day_str = day_date.strftime('%m/%d')
            days.append(day_str)
            
            count = reservation_dict.get(day_str, 0)
            reservation_counts.append(count)
        
        return jsonify({
            'revenue': {
                'months': months,
                'revenue': revenue
            },
            'utilization': {
                'lots': lot_names,
                'utilization': utilization_rates
            },
            'trends': {
                'days': days,
                'reservations': reservation_counts
            }
        })
        
    except Exception as e:
        print(f"Admin statistics error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': 'Internal server error', 'error': str(e)}), 500


# === USER ROUTES ===
@app.route('/api/parking-lots', methods=['GET'])
@jwt_required()
def get_parking_lots():
    cache_key = get_cache_key('parking_lots')
    cached_data = cache_get(cache_key)
    
    if cached_data:
        return jsonify(cached_data)
    
    lots = ParkingLot.query.all()
    lots_data = []
    
    for lot in lots:
        available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
        lots_data.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'price': lot.price,
            'address': lot.address,
            'pin_code': lot.pin_code,
            'number_of_spots': lot.number_of_spots,
            'available_spots': available_spots
        })
    
    cache_set(cache_key, lots_data, 60)
    return jsonify(lots_data)
    
@app.route('/api/reserve-spot', methods=['POST'])
@jwt_required()
def reserve_spot():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'lot_id' not in data or 'vehicle_number' not in data:
        return jsonify({'message': 'Missing required fields'}), 400
    
    lot_id = data['lot_id']
    vehicle_number = data['vehicle_number']
    
    try:
        existing_reservation = db.session.execute(
            db.text("SELECT id FROM reservation WHERE user_id = :user_id AND status = 'active'"),
            {'user_id': user_id}
        ).first()
        
        if existing_reservation:
            return jsonify({'message': 'You already have an active reservation'}), 400
    except Exception as e:
        print(f"Error checking existing reservations: {e}")
    
    spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').first()
    if not spot:
        return jsonify({'message': 'No available spots'}), 400
    
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({'message': 'Parking lot not found'}), 404

    try:
        reservation_data = {
            'spot_id': spot.id,
            'user_id': user_id,
            'vehicle_number': vehicle_number,
            'parking_cost': lot.price,  # Set basic cost
            'status': 'active'
        }
        
        try:
            db.session.execute(db.text("SELECT base_cost FROM reservation LIMIT 1"))
            temp_reservation = type('obj', (object,), {
                'parking_timestamp': datetime.utcnow()
            })()
            
            initial_breakdown = calculate_parking_cost(temp_reservation, lot.price, temp_reservation.parking_timestamp)
            
            reservation_data.update({
                'hourly_rate': lot.price,
                'base_cost': lot.price,
                'total_hours': 1.0,
                'cost_breakdown': json.dumps(initial_breakdown)
            })
        except Exception:
            print("New columns not found, creating basic reservation")
        
        reservation = Reservation(**reservation_data)
        
        spot.status = 'O'
        
        db.session.add(reservation)
        db.session.commit()
        
        redis_client.delete(get_cache_key('parking_lots'))
        
        return jsonify({
            'message': 'Spot reserved successfully',
            'reservation_id': reservation.id,
            'spot_number': spot.spot_number,
            'initial_cost': lot.price,
            'lot_name': lot.prime_location_name
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating reservation: {str(e)}")
        return jsonify({'message': 'Failed to create reservation'}), 500

@app.route('/api/release-spot/<int:reservation_id>', methods=['PUT'])
@jwt_required()
def release_spot(reservation_id):
    user_id = get_jwt_identity()
    reservation = Reservation.query.get_or_404(reservation_id)

    print("JWT identity:", get_jwt_identity(), type(get_jwt_identity()))
    print("Reservation user_id:", reservation.user_id, type(reservation.user_id))
    print(reservation.user_id == user_id)
    
    if reservation.user_id != int(user_id):
        return jsonify({'message': 'Unauthorized'}), 403
    
    if reservation.status == 'completed':
        return jsonify({'message': 'Spot already released'}), 400
    
    leaving_time = datetime.utcnow()
    reservation.leaving_timestamp = leaving_time

    cost_breakdown = calculate_parking_cost(reservation, reservation.hourly_rate, leaving_time)

    reservation.leaving_timestamp = datetime.utcnow()
    duration = (reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 3600

    reservation.parking_cost = cost_breakdown['total_cost']
    
    reservation.total_hours = cost_breakdown['total_hours']
    reservation.cost_breakdown = json.dumps(cost_breakdown)
    reservation.status = 'parked out'
    
    reservation.spot.status = 'A'
    
    db.session.commit()
    
    redis_client.delete(get_cache_key('parking_lots'))
    
    return jsonify({
        'message': 'Spot released successfully',
        'cost_breakdown': cost_breakdown,
        'total_cost': reservation.parking_cost,
        'duration_hours': duration
    })

@app.route('/api/user-reservations', methods=['GET'])
@jwt_required()
def get_user_reservations():
    user_id = get_jwt_identity()
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(
        Reservation.parking_timestamp.desc()
    ).all()
    
    reservations_data = []
    for res in reservations:
        try:
            if res.cost_breakdown:
                breakdown = json.loads(res.cost_breakdown)
            else:
                breakdown = {
                    'total_cost': res.parking_cost or 0,
                    'hourly_rate': res.hourly_rate or 0,
                    'total_hours': res.total_hours or 0
                }

            if res.status == 'active':
                current_breakdown = calculate_parking_cost(res, res.hourly_rate)
                breakdown.update(current_breakdown)

        except Exception as e:
            breakdown = {
                'base_cost': res.parking_cost or 0,
                'hourly_rate': res.spot.lot.price,
                'total_hours': 1.0,
                'additional_hours': 0,
                'additional_cost': 0,
                'total_cost': res.parking_cost or 0
            }

        reservations_data.append({
            'id': res.id,
            'spot_number': res.spot.spot_number,
            'lot_name': res.spot.lot.prime_location_name,
            'vehicle_number': res.vehicle_number,
            'parking_timestamp': res.parking_timestamp.isoformat(),
            'leaving_timestamp': res.leaving_timestamp.isoformat() if res.leaving_timestamp else None,
            'parking_cost': res.parking_cost,
            'status': res.status,
            'cost_breakdown': breakdown
        })
    
    return jsonify(reservations_data)

@app.route('/api/user/statistics', methods=['GET'])
@jwt_required()
def user_statistics():
    try:
        user_id = get_jwt_identity()
        
        # User monthly spending (last 6 months)
        from datetime import datetime, timedelta
        from sqlalchemy import func, extract
        
        six_months_ago = datetime.now() - timedelta(days=180)
        
        # Get spending data for completed reservations
        spending_data = db.session.query(
            extract('month', Reservation.leaving_timestamp).label('month'),
            extract('year', Reservation.leaving_timestamp).label('year'),
            func.sum(Reservation.parking_cost).label('total_spent')
        ).filter(
            Reservation.user_id == user_id,
            Reservation.leaving_timestamp >= six_months_ago,
            Reservation.status.in_(['completed', 'parked out']),
            Reservation.parking_cost.isnot(None)
        ).group_by(
            extract('year', Reservation.leaving_timestamp),
            extract('month', Reservation.leaving_timestamp)
        ).order_by(
            extract('year', Reservation.leaving_timestamp),
            extract('month', Reservation.leaving_timestamp)
        ).all()
        
        months = []
        spending = []
        
        # If no spending data, provide default values for last 6 months
        if not spending_data:
            current_date = datetime.now()
            for i in range(6):
                month_date = current_date - timedelta(days=30*i)
                month_name = month_date.strftime('%B %Y')
                months.insert(0, month_name)
                spending.insert(0, 0)
        else:
            for row in spending_data:
                try:
                    month_date = datetime(int(row.year), int(row.month), 1)
                    month_name = month_date.strftime('%B %Y')
                    months.append(month_name)
                    spending.append(float(row.total_spent or 0))
                except Exception as e:
                    print(f"Error processing spending row: {e}")
                    continue
        
        # User parking duration distribution - get ALL user reservations
        user_reservations = Reservation.query.filter(
            Reservation.user_id == user_id,
            Reservation.status.in_(['completed', 'parked out']),
            Reservation.leaving_timestamp.isnot(None),
            Reservation.parking_timestamp.isnot(None)
        ).all()
        
        duration_buckets = [0, 0, 0, 0]  # <1h, 1-3h, 3-6h, 6+h
        
        print(f"User {user_id} has {len(user_reservations)} completed reservations")
        
        if user_reservations:
            for reservation in user_reservations:
                try:
                    duration_hours = (reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 3600
                    print(f"Reservation {reservation.id}: {duration_hours:.2f} hours")
                    
                    if duration_hours < 1:
                        duration_buckets[0] += 1
                    elif duration_hours < 3:
                        duration_buckets[1] += 1
                    elif duration_hours < 6:
                        duration_buckets[2] += 1
                    else:
                        duration_buckets[3] += 1
                except Exception as e:
                    print(f"Error calculating duration for reservation {reservation.id}: {e}")
                    continue
        
        print(f"Duration buckets: {duration_buckets}")
        
        # If all buckets are 0, show message data
        if sum(duration_buckets) == 0:
            duration_buckets = [0, 0, 0, 0]  # All zeros to show "No data"
        
        return jsonify({
            'spending': {
                'months': months,
                'spending': spending
            },
            'duration': {
                'durations': duration_buckets
            }
        })
        
    except Exception as e:
        print(f"User statistics error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': 'Internal server error', 'error': str(e)}), 500


# === REDIS ROUTES ===
@app.route('/api/cache-status', methods=['GET'])
@jwt_required()
def get_cache_status():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    return jsonify({
        'parkingLots': redis_client.exists(get_cache_key('parking_lots'))
    })

@app.route('/api/clear-cache', methods=['POST'])
@jwt_required()
def clear_cache():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    redis_client.flushdb()
    return jsonify({'message': 'Cache cleared successfully'})


# === CELERY ROUTES ===
@app.route('/api/download-csv/<download_key>', methods=['GET'])
@jwt_required()
def download_csv(download_key):
    csv_data = cache_get(download_key)
    if not csv_data:
        return jsonify({'message': 'File not found or expired'}), 404
    
    from flask import make_response
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=parking_data.csv'
    return response

@app.route('/api/export-csv', methods=['POST'])
@jwt_required()
def export_csv():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    from celery_app import export_user_data_csv
    task = export_user_data_csv.delay(user_id)
    
    return jsonify({
        'message': 'Export job started',
        'task_id': task.id,
        'user_id': user_id,
        'user_role': user.role
    }), 202

@app.route('/api/task-status/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'status': task.state,
                'progress': 0,
                'result': None
            }
        elif task.state == 'PROGRESS':
            response = {
                'status': task.state,
                'progress': task.info.get('progress', 0),
                'result': None
            }
        elif task.state == 'SUCCESS':
            response = {
                'status': task.state,
                'progress': 100,
                'result': task.result
            }
        elif task.state == 'FAILURE':
            response = {
                'status': task.state,
                'progress': 0,
                'result': None,
                'error': str(task.info)
            }
        else:
            response = {
                'status': task.state,
                'progress': 0,
                'result': task.result if hasattr(task, 'result') else None
            }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'progress': 0,
            'result': None,
            'error': str(e)
        }), 500

@app.route('/api/trigger-reminders', methods=['POST'])
@jwt_required()
def trigger_reminders():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    from celery_app import send_daily_reminders
    task = send_daily_reminders.delay()
    
    return jsonify({
        'task_id': task.id,
        'user_id': user_id,
        'user_role': user.role
    })

@app.route('/api/generate-reports', methods=['POST'])
@jwt_required()
def trigger_reports():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    from celery_app import generate_monthly_reports
    task = generate_monthly_reports.delay()
    
    return jsonify({
        'task_id': task.id,
        'user_id': user_id,
        'user_role': user.role
    })
    

# === Initialization ===
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_admin()
        migrate_existing_reservations() 
    app.run(debug=True, host='0.0.0.0', port=5000)