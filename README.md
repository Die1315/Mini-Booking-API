# Mini-Booking API

A Django REST API for managing farm inspection bookings with weather data integration and public holiday validation.

## Features

- **User Authentication**: Register and login with username/password
- **Booking Management**: Create, read, update, and delete farm inspection bookings
- **Weather Integration**: Automatic weather data fetching for booking locations
- **Public Holiday Validation**: Prevents bookings on public holidays
- **Notes System**: Add notes to bookings
- **Location-based**: Uses latitude/longitude for weather data

## Prerequisites

- Python 3.8+
- pip
- Git
- PostgreSQL 12+

## PostgreSQL Setup

1. **Install PostgreSQL**
   ```bash
   # On Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib
   
   # On macOS with Homebrew
   brew install postgresql
   
   # On Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. **Start PostgreSQL service**
   ```bash
   # On Ubuntu/Debian
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   
   # On macOS
   brew services start postgresql
   ```

3. **Create database and user**
   ```bash
   sudo -u postgres psql
   
   CREATE DATABASE mini_booking_db;
   CREATE USER mini_booking_user WITH PASSWORD 'your_password_here';
   GRANT ALL PRIVILEGES ON DATABASE mini_booking_db TO mini_booking_user;
   \q
   ```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd futurelab
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DB_NAME=mini_booking_db
   DB_USER=mini_booking_user
   DB_PASSWORD=your_password_here
   DB_HOST=localhost
   DB_PORT=5432
   WEATHER_API_URL=https://api.open-meteo.com/v1/forecast
   PUBLIC_HOLIDAYS_API_URL=https://date.nager.at/api/v3/PublicHolidays
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication

#### Register a new user
```http
POST /api/auth/register/
Content-Type: application/json

{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword123",
    "password_confirmation": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
}
```

**Response:**
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
}
```

#### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
    "username": "john_doe",
    "password": "securepassword123"
}
```

**Response:**
```json
{
    "token": "your-auth-token-here",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
}
```

### Bookings

**Note:** All booking endpoints require authentication. Include the token in the Authorization header:
```
Authorization: Token your-auth-token-here
```

#### List all bookings
```http
GET /api/bookings/
Authorization: Token your-auth-token-here
```

**Response:**
```json
[
    {
        "id": 1,
        "date_time": "2024-01-15T10:00:00Z",
        "duration": 60,
        "farm_name": "Green Valley Farm",
        "inspector_name": "John Smith",
        "latitude": "-36.8485",
        "longitude": "174.7633",
        "temperature": "22.50",
        "wind_speed": "15.20",
        "creator": 1,
        "notes": [
            {
                "id": 1,
                "content": "Initial inspection completed",
                "created_at": "2024-01-10T09:30:00Z"
            }
        ]
    }
]
```

#### Create a new booking
```http
POST /api/bookings/
Authorization: Token your-auth-token-here
Content-Type: application/json

{
    "date_time": "2024-01-20T14:00:00Z",
    "duration": 90,
    "farm_name": "Sunset Ranch",
    "inspector_name": "Jane Doe",
    "latitude": -36.8485,
    "longitude": 174.7633,
    "notes": [
        {"content": "Initial inspection scheduled"},
        {"content": "Equipment check required"},
        {"content": "Follow-up visit needed"}
    ]
}
```

**Response:**
```json
{
    "id": 2,
    "date_time": "2024-01-20T14:00:00Z",
    "duration": 90,
    "farm_name": "Sunset Ranch",
    "inspector_name": "Jane Doe",
    "latitude": "-36.8485",
    "longitude": "174.7633",
    "temperature": "24.30",
    "wind_speed": "12.80",
    "creator": 1,
    "notes": [
        {
            "id": 1,
            "content": "Initial inspection scheduled",
            "created_at": "2024-01-10T09:30:00Z"
        },
        {
            "id": 2,
            "content": "Equipment check required",
            "created_at": "2024-01-10T09:30:00Z"
        },
        {
            "id": 3,
            "content": "Follow-up visit needed",
            "created_at": "2024-01-10T09:30:00Z"
        }
    ]
}
```

#### Get a specific booking
```http
GET /api/bookings/1/
Authorization: Token your-auth-token-here
```

#### Update a booking (full update)
```http
PUT /api/bookings/1/
Authorization: Token your-auth-token-here
Content-Type: application/json

{
    "date_time": "2024-01-22T15:00:00Z",
    "duration": 120,
    "farm_name": "Updated Farm Name",
    "inspector_name": "Updated Inspector",
    "latitude": -37.8485,
    "longitude": 175.7633
}
```

#### Update a booking (partial update)
```http
PATCH /api/bookings/1/
Authorization: Token your-auth-token-here
Content-Type: application/json

{
    "farm_name": "Partially Updated Farm",
    "duration": 75
}
```

#### Delete a booking
```http
DELETE /api/bookings/1/
Authorization: Token your-auth-token-here
```

**Response:** 204 No Content

### Notes

Notes can be created, updated, and deleted when working with bookings using the `notes` field. The field is optional and accepts various formats:

#### Creating a booking without notes
```http
POST /api/bookings/
Authorization: Token your-auth-token-here
Content-Type: application/json

{
    "date_time": "2024-01-20T14:00:00Z",
    "duration": 90,
    "farm_name": "Sunset Ranch",
    "inspector_name": "Jane Doe",
    "latitude": -36.8485,
    "longitude": 174.7633
}
```

#### Creating a booking with empty notes array
```http
POST /api/bookings/
Authorization: Token your-auth-token-here
Content-Type: application/json

{
    "date_time": "2024-01-20T14:00:00Z",
    "duration": 90,
    "farm_name": "Sunset Ranch",
    "inspector_name": "Jane Doe",
    "latitude": -36.8485,
    "longitude": 174.7633,
    "notes": []
}
```

#### Creating notes with a booking
```http
POST /api/bookings/
Authorization: Token your-auth-token-here
Content-Type: application/json

{
    "date_time": "2024-01-20T14:00:00Z",
    "duration": 90,
    "farm_name": "Sunset Ranch",
    "inspector_name": "Jane Doe",
    "latitude": -36.8485,
    "longitude": 174.7633,
    "notes": [
        {"content": "Initial inspection scheduled"},
        {"content": "Equipment check required"}
    ]
}
```

#### Updating notes with a booking
```http
PUT /api/bookings/1/
Authorization: Token your-auth-token-here
Content-Type: application/json

{
    "date_time": "2024-01-20T14:00:00Z",
    "duration": 90,
    "farm_name": "Sunset Ranch",
    "inspector_name": "Jane Doe",
    "latitude": -36.8485,
    "longitude": 174.7633,
    "notes": [
        {"content": "Updated inspection notes"},
        {"content": "New equipment requirements"},
        {"content": "Additional follow-up needed"}
    ]
}
```

#### Removing all notes from a booking
```http
PATCH /api/bookings/1/
Authorization: Token your-auth-token-here
Content-Type: application/json

{
    "notes": []
}
```

#### Updating only notes (keeping other fields unchanged)
```http
PATCH /api/bookings/1/
Authorization: Token your-auth-token-here
Content-Type: application/json

{
    "notes": [
        {"content": "Only updating notes"},
        {"content": "Keeping other fields unchanged"}
    ]
}
```

#### Keeping existing notes unchanged
```http
PATCH /api/bookings/1/
Authorization: Token your-auth-token-here
Content-Type: application/json

{
    "farm_name": "Updated Farm Name",
    "duration": 120
}
```

#### Notes in booking response
```json
{
    "id": 1,
    "date_time": "2024-01-15T10:00:00Z",
    "farm_name": "Green Valley Farm",
    "notes": [
        {
            "id": 1,
            "content": "Initial inspection completed successfully",
            "created_at": "2024-01-10T09:30:00Z"
        },
        {
            "id": 2,
            "content": "Follow-up required for equipment maintenance",
            "created_at": "2024-01-10T10:15:00Z"
        }
    ]
}
```

## Data Models

### Booking
- `date_time`: DateTime when the inspection will take place
- `duration`: Duration in minutes
- `farm_name`: Name of the farm
- `inspector_name`: Name of the inspector
- `latitude`: Farm latitude (for weather data)
- `longitude`: Farm longitude (for weather data)
- `temperature`: Weather temperature (auto-populated)
- `wind_speed`: Wind speed (auto-populated)
- `creator`: User who created the booking

### Notes
- `content`: Note text
- `booking`: Related booking (foreign key)
- `created_at`: Timestamp when note was created

## Validation Rules

1. **Public Holidays**: Bookings cannot be made on public holidays (NZ holidays)
2. **Future Dates**: Bookings must be scheduled for future dates
3. **Authentication**: All booking operations require authentication
4. **Weather Data**: Temperature and wind speed are automatically fetched based on location and time

## Error Responses

### Validation Error (400)
```json
{
    "date_time": [
        "Booking date cannot be a public holiday."
    ]
}
```

### Authentication Error (401/403)
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### Not Found (404)
```json
{
    "detail": "Not found."
}
```

## Testing

Run the test suite:
```bash
python manage.py test
```

Run specific test classes:
```bash
python manage.py test bookings.tests.BookingTests
python manage.py test bookings.tests.NotesTests
```

## Docker Deployment

1. **Build the image**
   ```bash
   docker build -t mini-booking-api .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 mini-booking-api
   ```

## Docker Compose (Recommended)

For easier setup with PostgreSQL, use Docker Compose:

1. **Create .env file**
   Copy the example environment file and update the values:
   ```bash
   cp env.example .env
   ```
   
   Edit the `.env` file with your desired values:
   ```env
   # Django Settings
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   
   # Database Settings
   DB_NAME=mini_booking_db
   DB_USER=mini_booking_user
   DB_PASSWORD=your_password_here
   DB_HOST=localhost
   DB_PORT=5432
   
   # External APIs
   WEATHER_API_URL=https://api.open-meteo.com/v1/forecast
   PUBLIC_HOLIDAYS_API_URL=https://date.nager.at/api/v3/PublicHolidays
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

## Environment Variables

- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to False in production
- `DB_NAME`: PostgreSQL database name
- `DB_USER`: PostgreSQL database user
- `DB_PASSWORD`: PostgreSQL database password
- `DB_HOST`: PostgreSQL database host
- `DB_PORT`: PostgreSQL database port
- `WEATHER_API_URL`: Open-Meteo API URL
- `PUBLIC_HOLIDAYS_API_URL`: Public holidays API URL

## API Rate Limits

The application integrates with external APIs:
- **Weather API**: Open-Meteo (free tier)
- **Public Holidays API**: date.nager.at (free tier)

## Support

For issues and questions, please create an issue in the repository. 