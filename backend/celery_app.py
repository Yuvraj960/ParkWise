from celery import Celery
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

celery_app = Celery(
    'parkwise',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['celery_app']
)

# === Celery Configuration ===
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# === Email configuration ===
MAIL_CONFIG = {
    'MAIL_SERVER': 'smtp.gmail.com',
    'MAIL_PORT': 587,
    'MAIL_USERNAME': '23f2003857@ds.study.iitm.ac.in',
    'MAIL_PASSWORD': 'azka acvo kxgz cear',
    'MAIL_USE_TLS': True,
    'GCHAT_WEBHOOK_URL': 'https://chat.googleapis.com/v1/spaces/AAQAdVg03Bk/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=nXCgKXHud1RATZRA52e4vaIac-X6r9WpfzC3nN6v-MA'
}

# Helper functions
def send_email(to_email, subject, body, is_html=False):
    """Send email using SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = MAIL_CONFIG['MAIL_USERNAME']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
        
        server = smtplib.SMTP(MAIL_CONFIG['MAIL_SERVER'], MAIL_CONFIG['MAIL_PORT'])
        server.starttls()
        server.login(MAIL_CONFIG['MAIL_USERNAME'], MAIL_CONFIG['MAIL_PASSWORD'])
        text = msg.as_string()
        server.sendmail(MAIL_CONFIG['MAIL_USERNAME'], to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

def send_gchat_message(message):
    """Send message to Google Chat webhook"""
    try:
        import requests
        webhook_url = MAIL_CONFIG.get('GCHAT_WEBHOOK_URL')
        if not webhook_url:
            print("Google Chat webhook URL not configured")
            return False
            
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Google Chat message failed: {e}")
        return False

# Seperate Flask app and database models created for Celery tasks to fix module import issues
def create_flask_app():
    """Create Flask app with database configuration for Celery tasks"""
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from datetime import datetime
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    
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
    
    return app, db, User, ParkingLot, ParkingSpot, Reservation

@celery_app.task(bind=True)
def export_user_data_csv(self, user_id):
    """Export user parking data to CSV"""
    try:
        app, db, User, ParkingLot, ParkingSpot, Reservation = create_flask_app()
        
        with app.app_context():
            self.update_state(state='PROGRESS', meta={'progress': 10})
            
            import csv
            import io
            import json
            import redis
            
            redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            
            user = User.query.get(user_id)
            if not user:
                raise Exception(f"User with ID {user_id} not found")
            
            if user.role == 'admin':
                reservations = Reservation.query.join(ParkingSpot).join(ParkingLot).join(User).all()
            else:
                reservations = Reservation.query.filter_by(user_id=user_id).join(ParkingSpot).join(ParkingLot).all()
            
            self.update_state(state='PROGRESS', meta={'progress': 30})
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            if user.role == 'admin':
                writer.writerow([
                    'Reservation ID', 'User ID', 'Username', 'Email', 'Spot Number', 
                    'Lot Name', 'Lot Address', 'Vehicle Number', 'Parking Time', 
                    'Leaving Time', 'Duration (Hours)', 'Base Cost', 'Hourly Rate', 
                    'Total Cost', 'Status'
                ])
            else:
                writer.writerow([
                    'Reservation ID', 'Spot Number', 'Lot Name', 'Lot Address', 
                    'Vehicle Number', 'Parking Time', 'Leaving Time', 
                    'Duration (Hours)', 'Base Cost', 'Hourly Rate', 'Total Cost', 'Status'
                ])
            
            self.update_state(state='PROGRESS', meta={'progress': 50})
            
            for res in reservations:
                try:
                    if res.leaving_timestamp:
                        duration = (res.leaving_timestamp - res.parking_timestamp).total_seconds() / 3600
                        duration_str = f"{duration:.2f}"
                        leaving_time = res.leaving_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        duration = (datetime.utcnow() - res.parking_timestamp).total_seconds() / 3600
                        duration_str = f"{duration:.2f} (Active)"
                        leaving_time = 'Active'
                    
                    base_cost = res.parking_cost or 0
                    hourly_rate = res.spot.lot.price
                    
                    if hasattr(res, 'cost_breakdown') and res.cost_breakdown:
                        try:
                            breakdown = json.loads(res.cost_breakdown)
                            base_cost = breakdown.get('base_cost', base_cost)
                            hourly_rate = breakdown.get('hourly_rate', hourly_rate)
                            total_cost = breakdown.get('total_cost', res.parking_cost or 0)
                        except:
                            total_cost = res.parking_cost or 0
                    else:
                        total_cost = res.parking_cost or 0
                    
                    if user.role == 'admin':
                        row = [
                            res.id,
                            res.user_id,
                            res.user.username,
                            res.user.email,
                            res.spot.spot_number,
                            res.spot.lot.prime_location_name,
                            res.spot.lot.address,
                            res.vehicle_number,
                            res.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            leaving_time,
                            duration_str,
                            f"{base_cost:.2f}",
                            f"{hourly_rate:.2f}",
                            f"{total_cost:.2f}",
                            res.status
                        ]
                    else:
                        row = [
                            res.id,
                            res.spot.spot_number,
                            res.spot.lot.prime_location_name,
                            res.spot.lot.address,
                            res.vehicle_number,
                            res.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            leaving_time,
                            duration_str,
                            f"{base_cost:.2f}",
                            f"{hourly_rate:.2f}",
                            f"{total_cost:.2f}",
                            res.status
                        ]
                    
                    writer.writerow(row)
                    
                except Exception as row_error:
                    print(f"Error processing reservation {res.id}: {row_error}")
                    basic_row = [
                        res.id,
                        getattr(res.spot, 'spot_number', 'N/A'),
                        getattr(res.spot.lot, 'prime_location_name', 'N/A'),
                        res.vehicle_number or 'N/A',
                        res.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        leaving_time if 'leaving_time' in locals() else 'N/A',
                        res.parking_cost or 0,
                        res.status
                    ]
                    if user.role == 'admin':
                        basic_row.insert(1, res.user_id)
                        basic_row.insert(2, getattr(res.user, 'username', 'N/A'))
                    writer.writerow(basic_row)
            
            self.update_state(state='PROGRESS', meta={'progress': 80})
            
            csv_data = output.getvalue()
            output.close()
            
            print(f"Generated CSV data length: {len(csv_data)} characters")
            print(f"Number of reservations processed: {len(reservations)}")
            
            if len(csv_data) < 100:
                print("Warning: CSV data seems too small")
                print(f"CSV content preview: {csv_data[:200]}")
            
            cache_key = f"csv_export_{user_id}_{datetime.utcnow().timestamp()}"
            redis_client.setex(cache_key, 3600, json.dumps(csv_data))
            
            self.update_state(state='PROGRESS', meta={'progress': 100})
            
            return {
                'status': 'completed', 
                'download_key': cache_key,
                'records_count': len(reservations),
                'user_role': user.role
            }
        
    except Exception as e:
        print(f"CSV export error: {str(e)}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery_app.task(bind=True)
def send_daily_reminders(self):
    """Send daily reminders to users"""
    try:
        app, db, User, ParkingLot, ParkingSpot, Reservation = create_flask_app()
        
        with app.app_context():
            self.update_state(state='PROGRESS', meta={'progress': 10})
            
            users = User.query.filter_by(role='user').all()
            sent_count = 0
            
            for i, user in enumerate(users):
                active_reservations = Reservation.query.filter_by(
                    user_id=user.id, status='active'
                ).count()
                
                if active_reservations == 0:
                    subject = "ParkWise Daily Reminder"
                    body = f"""
                    Hi {user.username},
                    
                    You don't have any active parking reservations today.
                    Don't forget to book a parking spot if you're planning to visit!
                    
                    Visit our app to make a reservation.
                    
                    Best regards,
                    ParkWise Team
                    """
                    
                    if send_email(user.email, subject, body):
                        sent_count += 1
                        print(f"Reminder sent to {user.email}")
                    
                    gchat_message = f"Daily Reminder: {user.username} ({user.email}) has no active parking reservations."
                    send_gchat_message(gchat_message)
                
                progress = int((i + 1) / len(users) * 90) + 10
                self.update_state(state='PROGRESS', meta={'progress': progress})
            
            self.update_state(state='PROGRESS', meta={'progress': 100})
            return f"Reminders sent to {sent_count} users out of {len(users)}"
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery_app.task(bind=True)
def generate_monthly_reports(self):
    """Generate monthly activity reports"""
    try:
        app, db, User, ParkingLot, ParkingSpot, Reservation = create_flask_app()
        
        with app.app_context():
            self.update_state(state='PROGRESS', meta={'progress': 10})
            
            today = datetime.utcnow()
            first_day_current_month = today.replace(day=1)
            last_day_previous_month = first_day_current_month - timedelta(days=1)
            first_day_previous_month = last_day_previous_month.replace(day=1)
            
            users = User.query.filter_by(role='user').all()
            sent_count = 0
            
            for i, user in enumerate(users):
                reservations = Reservation.query.filter(
                    Reservation.user_id == user.id,
                    Reservation.parking_timestamp >= first_day_previous_month,
                    Reservation.parking_timestamp <= last_day_previous_month
                ).all()
                
                if reservations:
                    total_bookings = len(reservations)
                    total_cost = sum(res.parking_cost or 0 for res in reservations)
                    
                    lot_usage = {}
                    for res in reservations:
                        lot_name = res.spot.lot.prime_location_name
                        lot_usage[lot_name] = lot_usage.get(lot_name, 0) + 1
                    
                    most_used_lot = max(lot_usage.items(), key=lambda x: x[1])[0] if lot_usage else "None"
                    
                    subject = f"Monthly Parking Report - {last_day_previous_month.strftime('%B %Y')}"
                    body = f"""
                    <html>
                    <body>
                        <h2>Monthly Parking Report for {user.username}</h2>
                        <h3>Report Period: {first_day_previous_month.strftime('%B %d, %Y')} - {last_day_previous_month.strftime('%B %d, %Y')}</h3>
                        
                        <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0;">
                            <h3>Summary</h3>
                            <ul>
                                <li><strong>Total Bookings:</strong> {total_bookings}</li>
                                <li><strong>Total Cost:</strong> ${total_cost:.2f}</li>
                                <li><strong>Most Used Lot:</strong> {most_used_lot}</li>
                                <li><strong>Average Cost per Booking:</strong> ${total_cost/total_bookings:.2f}</li>
                            </ul>
                        </div>
                        
                        <h3>Booking Details</h3>
                        <table border="1" style="border-collapse: collapse; width: 100%;">
                            <tr style="background-color: #e0e0e0;">
                                <th>Date</th>
                                <th>Location</th>
                                <th>Spot</th>
                                <th>Vehicle</th>
                                <th>Cost</th>
                            </tr>
                    """
                    
                    for res in reservations:
                        body += f"""
                            <tr>
                                <td>{res.parking_timestamp.strftime('%Y-%m-%d')}</td>
                                <td>{res.spot.lot.prime_location_name}</td>
                                <td>{res.spot.spot_number}</td>
                                <td>{res.vehicle_number}</td>
                                <td>${res.parking_cost:.2f}</td>
                            </tr>
                        """
                    
                    body += """
                        </table>
                        
                        <p style="margin-top: 30px;">
                            Thank you for using ParkWise!<br>
                            <strong>ParkWise Team</strong>
                        </p>
                    </body>
                    </html>
                    """
                    
                    if send_email(user.email, subject, body, is_html=True):
                        sent_count += 1
                        print(f"Monthly report sent to {user.email}")
                
                progress = int((i + 1) / len(users) * 90) + 10
                self.update_state(state='PROGRESS', meta={'progress': progress})
            
            self.update_state(state='PROGRESS', meta={'progress': 100})
            return f"Monthly reports sent to {sent_count} users"
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

if __name__ == '__main__':
    celery_app.start()
