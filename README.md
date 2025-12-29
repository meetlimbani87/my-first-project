# Crime Report Management System

A production-ready FastAPI backend system for managing crime reports with secure role-based access control (RBAC), admin approval workflows, and comprehensive audit logging.

## Overview

This system implements a three-tier role hierarchy (USER, ADMIN, SUPER_ADMIN) with strict authorization rules and database persistence. It provides complete crime report lifecycle management from creation through investigation to resolution.

## Features

- **User Authentication**: Session-based authentication with bcrypt password hashing
- **Role-Based Access Control**: Three-tier role system (USER, ADMIN, SUPER_ADMIN)
- **Crime Report Management**: Create, view, update, and manage crime reports
- **Admin Approval Workflow**: Users can request Admin role, Super Admins approve/reject
- **Status Tracking**: Track report status changes through complete history
- **Audit Logging**: Comprehensive logging of all critical system actions
- **Soft Deletes**: Reports are soft-deleted for data integrity
- **API Documentation**: Interactive Swagger UI and ReDoc documentation

## Tech Stack

- **Backend Framework**: FastAPI 0.115.0
- **Database**: PostgreSQL 14+ with async SQLAlchemy 2.0
- **Authentication**: Session-based OAuth2 with passlib bcrypt
- **Validation**: Pydantic 2.9
- **Documentation**: OpenAPI/Swagger (FastAPI default)

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- pip or virtualenv for package management

## Installation

### 1. Clone Repository

```bash
cd my-first-project
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` file with your configuration:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/crime_db

# Security
SECRET_KEY=your-secret-key-here-change-in-production
SESSION_EXPIRY_HOURS=24

# Super Admin (for seeding)
SUPER_ADMIN_EMAIL=admin@example.com
SUPER_ADMIN_PASSWORD=change-me-in-production
```

### 5. Create Database

```bash
createdb crime_db
```

Or via PostgreSQL:

```sql
CREATE DATABASE crime_db;
```

### 6. Initialize Database and Seed Super Admin

```bash
python seed_superadmin.py
```

This will:
- Create all database tables
- Create initial Super Admin user
- Display credentials for login

## Running the Application

### Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at: http://localhost:8000

## API Documentation

Once the application is running, access interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
my-first-project/
├── app/
│   ├── main.py                      # FastAPI app entry point
│   ├── core/
│   │   ├── config.py                # Environment config & settings
│   │   ├── security.py              # Password hashing, token generation
│   │   └── database.py              # Database connection & session
│   ├── models/
│   │   ├── user.py                  # User model
│   │   ├── session.py               # Session model
│   │   ├── crime_report.py          # CrimeReport model
│   │   ├── admin_request.py         # AdminRequest model
│   │   ├── report_status_history.py # ReportStatusHistory model
│   │   └── audit_log.py             # AuditLog model
│   ├── schemas/
│   │   ├── user.py                  # User Pydantic schemas
│   │   ├── crime_report.py          # Report Pydantic schemas
│   │   ├── admin_request.py         # Admin request Pydantic schemas
│   │   └── audit_log.py             # Audit log Pydantic schemas
│   ├── routes/
│   │   ├── auth.py                  # Authentication endpoints
│   │   ├── users.py                 # User management endpoints
│   │   ├── reports.py               # Crime report endpoints
│   │   ├── admin.py                 # Admin control endpoints
│   │   └── audit.py                 # Audit log endpoints
│   ├── services/
│   │   ├── auth_service.py          # Auth business logic
│   │   ├── report_service.py        # Report business logic
│   │   ├── admin_service.py         # Admin workflow logic
│   │   └── audit_service.py         # Audit logging logic
│   └── dependencies/
│       └── auth.py                  # Auth dependencies
├── .env                             # Environment variables (git-ignored)
├── .env.example                     # Example environment variables
├── requirements.txt                 # Python dependencies
├── seed_superadmin.py               # Script to create Super Admin
└── README.md                        # This file
```

## Role Hierarchy

### USER (Default Role)
- Register and login
- Create crime reports
- View own reports (full details)
- View all reports (brief summary only)
- Request Admin role upgrade

### ADMIN (Approval Required)
- All USER permissions
- View any report (full details including admin notes)
- Update report status and priority
- Add admin notes to reports
- Soft delete reports
- View status history for any report

### SUPER_ADMIN (System-Level Only)
- All ADMIN permissions
- View all admin requests
- Approve/reject admin role requests
- Revoke Admin role from users
- Lock/unlock user accounts
- View comprehensive audit logs
- Cannot be created via API (seed script only)

## API Endpoints Overview

### Authentication (`/auth`)
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get session token
- `POST /auth/logout` - Logout and invalidate session
- `GET /auth/me` - Get current user profile

### Users (`/users`)
- `GET /users/profile` - Get detailed profile
- `POST /users/request-admin` - Request Admin role
- `GET /users/admin-request-status` - Check request status

### Reports (`/reports`)
- `POST /reports` - Create new report
- `GET /reports` - List all reports (brief)
- `GET /reports/my-reports` - Get own reports
- `GET /reports/{id}` - Get report details
- `PATCH /reports/{id}/status` - Update status (Admin)
- `PATCH /reports/{id}/priority` - Update priority (Admin)
- `PATCH /reports/{id}/notes` - Update admin notes (Admin)
- `DELETE /reports/{id}` - Soft delete report (Admin)
- `GET /reports/{id}/history` - Get status history

### Admin (`/admin`)
- `GET /admin/requests` - View all admin requests (Super Admin)
- `POST /admin/requests/{id}/approve` - Approve request (Super Admin)
- `POST /admin/requests/{id}/reject` - Reject request (Super Admin)
- `POST /admin/users/{id}/revoke-admin` - Revoke Admin (Super Admin)
- `POST /admin/users/{id}/lock` - Lock account (Super Admin)
- `POST /admin/users/{id}/unlock` - Unlock account (Super Admin)

### Audit (`/audit`)
- `GET /audit/logs` - View audit logs (Super Admin)
- `GET /audit/users/{id}` - View user's audit logs (Super Admin)

## Testing the API

### Using Swagger UI (Recommended)

1. Navigate to http://localhost:8000/docs
2. Click "Authorize" button
3. Login as Super Admin using seeded credentials
4. Test endpoints interactively

### Using curl

```bash
# Register a new user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"password123"}'

# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"password123"}'

# Create report (use session_token from login)
curl -X POST "http://localhost:8000/reports" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Report","description":"Test description"}'
```

## Security Notes

### Production Checklist

- [ ] Change `SECRET_KEY` in .env to strong random value
- [ ] Change Super Admin credentials immediately after seeding
- [ ] Set `ENVIRONMENT=production` in .env
- [ ] Enable HTTPS/TLS in production
- [ ] Configure CORS `ALLOWED_ORIGINS` appropriately
- [ ] Use strong database password
- [ ] Never commit `.env` file to version control
- [ ] Review and adjust `SESSION_EXPIRY_HOURS` as needed
- [ ] Set up proper database backups
- [ ] Configure firewall rules for PostgreSQL

### Security Features

- Bcrypt password hashing with automatic salt
- Session-based authentication with expiry
- Role-based access control (RBAC)
- Input validation via Pydantic
- SQL injection protection via SQLAlchemy ORM
- Security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection)
- Soft deletes for data integrity
- Comprehensive audit logging

## Database Schema

### Tables

- **users** - User accounts with roles and status
- **sessions** - Active sessions for authentication
- **crime_reports** - Crime report records
- **admin_requests** - Admin role upgrade requests
- **report_status_history** - Status change tracking
- **audit_logs** - System-wide audit trail

### Enums

- **UserRole**: USER, ADMIN, SUPER_ADMIN
- **ReportStatus**: NEW, ASSIGNED, INVESTIGATING, RESOLVED, CLOSED
- **ReportPriority**: LOW, MEDIUM, HIGH, CRITICAL
- **AdminRequestStatus**: PENDING, APPROVED, REJECTED

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Test connection
psql -U postgres -d crime_db
```

### Module Import Errors

```bash
# Ensure you're in virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use

```bash
# Use different port
uvicorn app.main:app --port 8001
```

## License

This project is provided as-is for educational and production use.

## Support

For issues and questions, refer to:
- API Documentation: http://localhost:8000/docs
- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
