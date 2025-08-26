# 🏙️ ParkWise - Smart Parking Management System

A comprehensive parking management solution built with Vue.js frontend and Flask backend, featuring real-time reservation tracking, automated reporting, and admin controls.

## ✨ Features

### 🚗 **User Features**
- **Account Management**: Secure registration and login system
- **Parking Lot Discovery**: Browse available parking lots with real-time availability
- **Smart Reservations**: Book parking spots instantly with vehicle registration
- **Live Tracking**: Monitor active reservations and parking duration
- **Cost Calculation**: Automatic pricing based on parking duration
- **Data Export**: Download personal parking history as CSV files
- **Background Tasks**: Real-time progress tracking for data exports

### 👨‍💼 **Admin Features**
- **Parking Lot Management**: Create, update, and delete parking facilities
- **Dynamic Spot Control**: Add or remove parking spots with occupancy validation
- **User Management**: View all registered users and their activity
- **Reservation Oversight**: Monitor all reservations across all locations
- **Analytics Dashboard**: Real-time statistics and occupancy insights
- **Automated Communications**: 
  - Daily reminder emails for users without active reservations
  - Monthly parking reports with usage analytics
  - Google Chat notifications for admin alerts
- **Performance Optimization**: Redis caching with manual cache control
- **Background Task Management**: Monitor system-wide background processes

### 🔧 **Technical Features**
- **Asynchronous Processing**: Celery-powered background tasks for heavy operations
- **Real-time Updates**: Live task progress monitoring with WebSocket-like polling
- **Secure Authentication**: JWT-based authentication with role-based access control
- **Data Persistence**: SQLite database with SQLAlchemy ORM
- **Email Integration**: SMTP-based automated email notifications
- **Caching Layer**: Redis for performance optimization
- **Responsive Design**: Mobile-friendly Tailwind CSS interface
- **RESTful API**: Clean, documented API endpoints

## Tech Stack

- Flask
- VueJS
- Jinja2
- SQLite
- Redis
- Celery

## 🏗️ Architecture

```
Frontend (Vue.js 3)          Backend (Flask)              Services
├── Vue Router               ├── JWT Authentication       ├── Redis Cache
├── Pinia State Management   ├── SQLAlchemy ORM          ├── Celery Workers
├── Axios HTTP Client        ├── CORS Support            ├── SMTP Email
├── Tailwind CSS            ├── Background Tasks         └── Google Chat
└── Real-time UI Updates    └── RESTful API                  Webhooks
```

## 📋 Prerequisites

Before running the application, ensure you have the following installed:

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Redis Server** (for caching and task queue)
- **Git** (for cloning the repository)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd ParkWise
```

### 2. Backend Setup

#### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### Configure Email Settings (Optional)
Edit `backend/celery_app.py` and `backend/main.py` to update email credentials:
```python
MAIL_CONFIG = {
    'MAIL_USERNAME': 'your-email@gmail.com',
    'MAIL_PASSWORD': 'your-app-password',
    # ... other settings
}
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

### 4. Start Redis Server
```bash
# On Windows (if installed via Chocolatey or manual install)
redis-server

# On macOS (if installed via Homebrew)
brew services start redis

# On Linux
sudo systemctl start redis
# or
redis-server
```

### 5. Launch the Application

**Terminal 1 - Flask Backend:**
```bash
cd backend
python main.py
```
> Backend will run on http://localhost:5000

**Terminal 2 - Celery Worker:**
```bash
cd backend
python start_celery.py
```

**Terminal 3 - Vue Frontend:**
```bash
cd frontend
npm run dev
```
> Frontend will run on http://localhost:5173

## 👤 Default Admin Account

The application automatically creates an admin account on first run:
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@parking.com`

## 🎯 Usage Guide

### For Regular Users:
1. **Register** a new account or **login** with existing credentials
2. **Browse** available parking lots on the "Parking Lots" page
3. **Reserve** a spot by clicking "Book Spot" and entering vehicle details
4. **Monitor** your active reservations in "My Bookings"
5. **Release** spots when leaving to stop billing
6. **Export** your parking history from the "Export Data" page

### For Administrators:
1. **Login** with admin credentials
2. **Manage** parking lots from the dashboard (create, edit, delete)
3. **Monitor** all user reservations and system activity
4. **View** user management and analytics
5. **Trigger** automated reports and reminders from "Admin Reports"
6. **Control** system cache and background tasks

## 🛠️ API Documentation

### Authentication Endpoints
- `POST /api/register` - User registration
- `POST /api/login` - User authentication

### Parking Management
- `GET /api/parking-lots` - List all parking lots
- `POST /api/parking-lots` - Create new lot (Admin)
- `PUT /api/parking-lots/{id}` - Update lot (Admin)
- `DELETE /api/parking-lots/{id}` - Delete lot (Admin)

### Reservations
- `POST /api/reserve-spot` - Book a parking spot
- `PUT /api/release-spot/{id}` - Release a reservation
- `GET /api/user-reservations` - Get user's reservations
- `GET /api/all-reservations` - Get all reservations (Admin)

### Background Tasks
- `POST /api/export-csv` - Export user data
- `POST /api/trigger-reminders` - Send daily reminders (Admin)
- `POST /api/generate-reports` - Generate monthly reports (Admin)
- `GET /api/task-status/{task_id}` - Check task progress

## 🐛 Troubleshooting

### Common Issues:

**Celery Tasks Not Working:**
- Ensure Redis is running on port 6379
- Check that Celery worker is started with the correct command
- Verify Python path includes the backend directory

**Frontend Styles Not Loading:**
- Run `npm install` in the frontend directory
- Check that Tailwind CSS is properly configured
- Clear browser cache and restart development server

**Database Issues:**
- Delete `instance/parking_app.db` to reset the database
- Restart the Flask application to recreate tables

**Email Notifications Not Sending:**
- Update email credentials in `backend/celery_app.py`
- Ensure "Less secure app access" is enabled for Gmail accounts
- Consider using App Passwords for Gmail

## 📁 Project Structure

```
ParkWise/
├── backend/
│   ├── main.py                 # Flask application and API routes
│   ├── celery_app.py          # Celery tasks and email functions
│   ├── start_celery.py        # Celery startup script
│   ├── requirements.txt       # Python dependencies
│   └── instance/
│       └── parking_app.db     # SQLite database
└── frontend/
    ├── src/
    │   ├── components/       # Vue components
    │   ├── pages/            # Page components
    │   ├── assets/           # Static assets (css, images, fonts, etc)
    │   ├── services/         # API service layers
    │   ├── store/           # Pinia state management
    │   └── router/          # Vue Router configuration
    ├── package.json         # Node.js dependencies
    └── tailwind.config.js   # Tailwind CSS configuration
```
