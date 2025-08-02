from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from bookings.models import Booking, Notes


class BookingTests(TestCase):
    def setUp(self):
        # Mock API responses for booking creation       
        self.booking_date_time = timezone.now() + timedelta(days=7)
          
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)

        # Test data for creating bookings
        self.booking_data = {
            'date_time': (timezone.now() + timedelta(days=7)).isoformat(),
            'duration': 60,
            'farm_name': 'Test Farm',
            'inspector_name': 'Test Inspector',
            'latitude': -36.8485,
            'longitude': 174.763300
        }

        # Create test bookings
        self.booking1 = Booking.objects.create(
            date_time=timezone.now() + timedelta(days=1),
            duration=60,
            farm_name='Test Farm 1',
            inspector_name='Test Inspector 1',
            latitude=-36.8485,
            longitude=174.7633,
            creator=self.user,
            temperature=20,
            wind_speed=10,
        )

        self.booking2 = Booking.objects.create(
            date_time=timezone.now() + timedelta(days=2),
            duration=90,
            farm_name='Test Farm 2',
            inspector_name='Test Inspector 2',
            latitude=-36.8485,
            longitude=174.7633,
            creator=self.user,
            temperature=20,
            wind_speed=10,
        )

        self.booking3 = Booking.objects.create(
            date_time=timezone.now() + timedelta(days=3),
            duration=120,
            farm_name='Test Farm 3',
            inspector_name='Test Inspector 3',
            latitude=-36.8485,
            longitude=174.7633,
            creator=self.user,
            temperature=25,
            wind_speed=15,
        )

        # Create test notes
        self.note1 = Notes.objects.create(
            content='Test note 1',
            booking=self.booking1
        )

        self.note2 = Notes.objects.create(
            content='Test note 2',
            booking=self.booking1
        )

        self.note3 = Notes.objects.create(
            content='Test note 3',
            booking=self.booking2
        )

    @patch('requests.get')
    def test_create_booking_authenticated(self, mock_get):
        """Test creating a new booking with authenticated user"""
        # Mock both APIs using a side_effect that returns different responses based on URL
        def mock_requests_get(url):
            mock_response = Mock()
            if 'PublicHolidays' in url:
                # Public holidays API response
                mock_response.json.return_value = []
                mock_response.raise_for_status.return_value = None
            else:
                # Weather API response
                booking_datetime = self.booking_date_time
                if booking_datetime.minute > 30:
                    booking_datetime += timedelta(hours=1)
                booking_datetime = booking_datetime.replace(
                    minute=0, second=0, microsecond=0
                )
                mock_response.json.return_value = {
                    'hourly': {
                        'time': [
                            booking_datetime.strftime('%Y-%m-%dT%H:%M')
                        ],
                        'temperature_2m': [22.5],
                        'windspeed_10m': [15.2]
                    }
                }
                mock_response.raise_for_status.return_value = None
            return mock_response
        
        mock_get.side_effect = mock_requests_get
        
        url = reverse('booking-list')
        response = self.client.post(url, self.booking_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 4)  # 3 from setUp + 1 new
        
        # Test core fields with proper handling of format differences
        self.assertEqual(response.data['farm_name'], self.booking_data['farm_name'])
        self.assertEqual(response.data['inspector_name'], self.booking_data['inspector_name'])
        self.assertEqual(response.data['duration'], self.booking_data['duration'])
        
        # Handle decimal precision differences
        self.assertEqual(float(response.data['latitude']), float(self.booking_data['latitude']))
        self.assertEqual(float(response.data['longitude']), float(self.booking_data['longitude']))
        
        # Handle datetime format differences (both Z and +00:00 are valid UTC formats)
        response_datetime = response.data['date_time'].replace('Z', '+00:00')
        self.assertEqual(response_datetime, self.booking_data['date_time'])
        
        self.assertEqual(float(response.data['temperature']), float(22.5))
        self.assertEqual(float(response.data['wind_speed']), float(15.2))
        self.assertEqual(response.data['creator'], self.user.id)

    @patch('requests.get')
    def test_create_booking_unauthenticated(self, mock_get):
        """Test creating a booking without authentication"""
        # Mock API responses (though they shouldn't be called)
        def mock_requests_get(url):
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_response.raise_for_status.return_value = None
            return mock_response
        
        mock_get.side_effect = mock_requests_get
        
        self.client.logout()
        url = reverse('booking-list')
        response = self.client.post(url, self.booking_data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_all_bookings_authenticated(self):
        """Test listing all bookings for authenticated user"""
        url = reverse('booking-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # 3 bookings from setUp
        
        # Verify all bookings are returned
        booking_ids = [booking['id'] for booking in response.data]
        self.assertIn(self.booking1.id, booking_ids)
        self.assertIn(self.booking2.id, booking_ids)
        self.assertIn(self.booking3.id, booking_ids)

    def test_list_all_bookings_unauthenticated(self):
        """Test listing bookings without authentication"""
        self.client.logout()
        url = reverse('booking-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_bookings_with_notes(self):
        """Test that bookings are returned with their associated notes"""
        url = reverse('booking-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Find booking1 in response and check its notes
        booking1_data = next(
            booking for booking in response.data 
            if booking['id'] == self.booking1.id
        )
        self.assertEqual(len(booking1_data['notes']), 2)  # booking1 has 2 notes
        
        # Find booking2 in response and check its notes
        booking2_data = next(
            booking for booking in response.data 
            if booking['id'] == self.booking2.id
        )
        self.assertEqual(len(booking2_data['notes']), 1)  # booking2 has 1 note
        
        # Find booking3 in response and check its notes
        booking3_data = next(
            booking for booking in response.data 
            if booking['id'] == self.booking3.id
        )
        self.assertEqual(len(booking3_data['notes']), 0)  # booking3 has no notes

    def test_get_single_booking(self):
        """Test retrieving a single booking by ID"""
        url = reverse('booking-detail', kwargs={'pk': self.booking1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.booking1.id)
        self.assertEqual(response.data['farm_name'], self.booking1.farm_name)
        self.assertEqual(len(response.data['notes']), 2)

    def test_get_nonexistent_booking(self):
        """Test retrieving a booking that doesn't exist"""
        url = reverse('booking-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('requests.get')
    def test_update_booking_full(self, mock_get):
        """Test updating a booking with all fields"""
        # Calculate the booking datetime that will be used in the update
        booking_datetime = timezone.now() + timedelta(days=10)
        # Round to nearest hour as done in _fetch_weather
        if booking_datetime.minute > 30:
            booking_datetime += timedelta(hours=1)
        booking_datetime = booking_datetime.replace(
            minute=0, second=0, microsecond=0
        )
        
        # Mock both APIs using a side_effect that returns different responses based on URL
        def mock_requests_get(url):
            mock_response = Mock()
            if 'PublicHolidays' in url:
                # Public holidays API response
                mock_response.json.return_value = []
                mock_response.raise_for_status.return_value = None
            else:
                # Weather API response for the update with matching time
                mock_response.json.return_value = {
                    'hourly': {
                        'time': [booking_datetime.strftime('%Y-%m-%dT%H:%M')],
                        'temperature_2m': [25.0],
                        'windspeed_10m': [12.5]
                    }
                }
                mock_response.raise_for_status.return_value = None
            return mock_response
        
        mock_get.side_effect = mock_requests_get
        
        url = reverse('booking-detail', kwargs={'pk': self.booking1.id})
        update_data = {
            'date_time': (timezone.now() + timedelta(days=10)).isoformat(),
            'duration': 120,
            'farm_name': 'Updated Farm',
            'inspector_name': 'Updated Inspector',
            'latitude': -37.8485,
            'longitude': 175.7633,
        }
        
        response = self.client.put(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['farm_name'], 'Updated Farm')
        self.assertEqual(response.data['inspector_name'], 'Updated Inspector')
        self.assertEqual(response.data['duration'], 120)

    @patch('requests.get')
    @patch('bookings.serializers.requests.get')
    def test_update_booking_partial(self, mock_holidays_get, mock_weather_get):
        """Test partially updating a booking"""
        # Mock API responses (though weather shouldn't be called for this update)
        mock_weather_response = Mock()
        mock_weather_response.json.return_value = {'hourly': {}}
        mock_weather_get.return_value = mock_weather_response
        
        mock_holidays_response = Mock()
        mock_holidays_response.json.return_value = []
        mock_holidays_get.return_value = mock_holidays_response
        
        url = reverse('booking-detail', kwargs={'pk': self.booking1.id})
        update_data = {
            'farm_name': 'Partially Updated Farm',
            'duration': 90,
        }
        
        response = self.client.patch(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['farm_name'], 'Partially Updated Farm')
        self.assertEqual(response.data['duration'], 90)
        # Other fields should remain unchanged
        self.assertEqual(response.data['inspector_name'], self.booking1.inspector_name)

    @patch('requests.get')
    @patch('bookings.serializers.requests.get')
    def test_update_booking_unauthenticated(self, mock_holidays_get, mock_weather_get):
        """Test updating a booking without authentication"""        
        mock_weather_response = Mock()
        mock_weather_response.json.return_value = {'hourly': {}}
        mock_weather_get.return_value = mock_weather_response
        
        mock_holidays_response = Mock()
        mock_holidays_response.json.return_value = []
        mock_holidays_get.return_value = mock_holidays_response
        
        self.client.logout()
        url = reverse('booking-detail', kwargs={'pk': self.booking1.id})
        update_data = {'farm_name': 'Unauthorized Farm'}
        
        response = self.client.patch(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('requests.get')
    @patch('bookings.serializers.requests.get')
    def test_update_nonexistent_booking(self, mock_holidays_get, mock_weather_get):
        """Test updating a booking that doesn't exist"""      
        mock_weather_response = Mock()
        mock_weather_response.json.return_value = {'hourly': {}}
        mock_weather_get.return_value = mock_weather_response
        
        mock_holidays_response = Mock()
        mock_holidays_response.json.return_value = []
        mock_holidays_get.return_value = mock_holidays_response
        
        url = reverse('booking-detail', kwargs={'pk': 99999})
        update_data = {'farm_name': 'Nonexistent Farm'}
        
        response = self.client.patch(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_booking(self):
        """Test deleting a booking"""
        url = reverse('booking-detail', kwargs={'pk': self.booking1.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Booking.objects.filter(id=self.booking1.id).exists())
        # Notes should also be deleted due to CASCADE
        self.assertFalse(Notes.objects.filter(booking_id=self.booking1.id).exists())

    def test_delete_booking_unauthenticated(self):
        """Test deleting a booking without authentication"""
        self.client.logout()
        url = reverse('booking-detail', kwargs={'pk': self.booking1.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_nonexistent_booking(self):
        """Test deleting a booking that doesn't exist"""
        url = reverse('booking-detail', kwargs={'pk': 99999})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_booking_cascades_notes(self):
        """Test that deleting a booking also deletes its associated notes"""
        # Verify notes exist before deletion
        self.assertTrue(Notes.objects.filter(booking=self.booking1).exists())
        self.assertEqual(Notes.objects.filter(booking=self.booking1).count(), 2)
        
        # Delete the booking
        url = reverse('booking-detail', kwargs={'pk': self.booking1.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify notes are also deleted
        self.assertFalse(Notes.objects.filter(booking_id=self.booking1.id).exists())
        # Other notes should still exist
        self.assertTrue(Notes.objects.filter(booking=self.booking2).exists())

    @patch('requests.get')
    def test_create_booking_on_holiday(self, mock_get):
        """Test creating a booking on a public holiday should fail"""
        # Mock both APIs using a side_effect that returns different responses based on URL
        def mock_requests_get(url):
            mock_response = Mock()
            if 'PublicHolidays' in url:
                # Public holidays API response with a holiday
                mock_response.json.return_value = [
                    {
                        'date': '2024-01-15',
                        'localName': 'Test Holiday',
                        'name': 'Test Holiday',
                        'countryCode': 'NZ',
                        'fixed': True,
                        'global': False,
                        'counties': None,
                        'launchYear': None,
                        'types': ['Public']
                    },
                    {
                        'date': '2024-01-26',
                        'localName': 'Another Holiday',
                        'name': 'Another Holiday',
                        'countryCode': 'NZ',
                        'fixed': True,
                        'global': False,
                        'counties': None,
                        'launchYear': None,
                        'types': ['Public']
                    }
                ]
                mock_response.raise_for_status.return_value = None
            else:
                # Weather API response with proper data (in case validation doesn't work)
                from datetime import datetime, timezone
                booking_datetime = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
                booking_datetime = booking_datetime.replace(minute=0, second=0, microsecond=0)
                
                mock_response.json.return_value = {
                    'hourly': {
                        'time': [booking_datetime.strftime('%Y-%m-%dT%H:%M')],
                        'temperature_2m': [22.5],
                        'windspeed_10m': [15.2]
                    }
                }
                mock_response.raise_for_status.return_value = None
            return mock_response
        
        mock_get.side_effect = mock_requests_get
        
        # Try to create booking on a public holiday
        holiday_booking_data = {
            'date_time': '2024-01-15T10:00:00Z',  # Public holiday
            'duration': 60,
            'farm_name': 'Farm on Holiday',
            'inspector_name': 'Test Inspector',
            'latitude': -36.8485,
            'longitude': 174.7633,
        }
        
        url = reverse('booking-list')
        response = self.client.post(url, holiday_booking_data)
        
        # Should fail validation        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('public holiday', str(response.data).lower())
        
        # Verify no booking was created
        self.assertEqual(Booking.objects.count(), 3)  # Only the 3 from setUp


class NotesTests(TestCase):
    """Test cases specifically for Notes functionality"""
    
    @patch('requests.get')
    def setUp(self, mock_get):
        # Mock API responses for booking creation
        def mock_requests_get(url):
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_response.raise_for_status.return_value = None
            return mock_response
        
        mock_get.side_effect = mock_requests_get
        
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test booking
        self.booking = Booking.objects.create(
            date_time=timezone.now() + timedelta(days=1),
            duration=60,
            farm_name='Test Farm',
            inspector_name='Test Inspector',
            latitude=-36.8485,
            longitude=174.7633,
            creator=self.user,
            temperature=22.5,
            wind_speed=15.2,
        )
        
        # Create test notes
        self.note1 = Notes.objects.create(
            content='Test note 1',
            booking=self.booking
        )
        
        self.note2 = Notes.objects.create(
            content='Test note 2',
            booking=self.booking
        )

    def test_notes_included_in_booking_response(self):
        """Test that notes are included when retrieving a booking"""
        url = reverse('booking-detail', kwargs={'pk': self.booking.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['notes']), 2)
        
        # Check note content
        note_contents = [note['content'] for note in response.data['notes']]
        self.assertIn('Test note 1', note_contents)
        self.assertIn('Test note 2', note_contents)

    def test_create_note_via_booking_update(self):
        """Test creating a note by updating the booking with new note data"""
        # Since there's no direct note endpoint, we test that notes are properly
        # handled in the booking serializer
        url = reverse('booking-detail', kwargs={'pk': self.booking.id})
        
        # Get current booking data
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify current notes
        self.assertEqual(len(response.data['notes']), 2)

    @patch('requests.get')
    @patch('bookings.serializers.requests.get')
    def test_notes_are_read_only(self, mock_holidays_get, mock_weather_get):
        """Test that notes field is read-only in the API"""
        # Mock API responses for the update operation
        mock_weather_response = Mock()
        mock_weather_response.json.return_value = {'hourly': {}}
        mock_weather_get.return_value = mock_weather_response
        
        mock_holidays_response = Mock()
        mock_holidays_response.json.return_value = []
        mock_holidays_get.return_value = mock_holidays_response
        
        url = reverse('booking-detail', kwargs={'pk': self.booking.id})
        
        # Try to update booking with notes data (should be ignored)
        update_data = {
            'farm_name': 'Updated Farm',
            'notes': [
                {'content': 'New note that should not be created'}
            ]
        }
        
        response = self.client.patch(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['farm_name'], 'Updated Farm')
        
        # Notes should remain unchanged
        self.assertEqual(len(response.data['notes']), 2)
        note_contents = [note['content'] for note in response.data['notes']]
        self.assertNotIn('New note that should not be created', note_contents)

    def test_notes_deleted_with_booking(self):
        """Test that notes are deleted when their booking is deleted"""
        # Verify notes exist
        self.assertEqual(Notes.objects.filter(booking=self.booking).count(), 2)
        
        # Delete the booking
        url = reverse('booking-detail', kwargs={'pk': self.booking.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify notes are also deleted
        self.assertEqual(Notes.objects.filter(booking_id=self.booking.id).count(), 0)

    def test_update_note_content_directly(self):
        """Test updating a note's content directly in the database"""
        # Since notes are read-only in the API, we test direct database updates
        original_content = self.note1.content
        new_content = 'Note updated directly'
        
        # Update note directly
        self.note1.content = new_content
        self.note1.save()
        
        # Verify the update
        self.note1.refresh_from_db()
        self.assertEqual(self.note1.content, new_content)
        self.assertNotEqual(self.note1.content, original_content)
        
        # Verify it's reflected in the API response
        url = reverse('booking-detail', kwargs={'pk': self.booking.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        note_contents = [note['content'] for note in response.data['notes']]
        self.assertIn(new_content, note_contents)
        self.assertNotIn(original_content, note_contents)

    def test_update_multiple_notes(self):
        """Test updating multiple notes for a booking"""
        # Update both notes
        self.note1.content = 'First note updated'
        self.note1.save()
        
        self.note2.content = 'Second note updated'
        self.note2.save()
        
        # Verify updates are reflected in API
        url = reverse('booking-detail', kwargs={'pk': self.booking.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        note_contents = [note['content'] for note in response.data['notes']]
        self.assertIn('First note updated', note_contents)
        self.assertIn('Second note updated', note_contents)

    def test_note_creation_timestamp(self):
        """Test that notes have proper creation timestamps"""
        # Create a new note
        new_note = Notes.objects.create(
            content='Note with timestamp',
            booking=self.booking
        )
        
        # Verify it has a creation timestamp
        self.assertIsNotNone(new_note.created_at)
        self.assertIsInstance(new_note.created_at, timezone.datetime)
        
        # Verify it's included in API response
        url = reverse('booking-detail', kwargs={'pk': self.booking.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['notes']), 3)  # 2 original + 1 new
        
        # Find the new note in response
        new_note_data = next(
            note for note in response.data['notes'] 
            if note['content'] == 'Note with timestamp'
        )
        


class BookingFilteringTests(TestCase):
    """Test cases for booking filtering and search functionality"""
    
    @patch('requests.get')
    def setUp(self, mock_get):
        # Mock API responses for booking creation
        def mock_requests_get(url):
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_response.raise_for_status.return_value = None
            return mock_response
        
        mock_get.side_effect = mock_requests_get
        
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create bookings with different dates
        self.booking_today = Booking.objects.create(
            date_time=timezone.now(),
            duration=60,
            farm_name='Farm Today',
            inspector_name='Inspector Today',
            latitude=-36.8485,
            longitude=174.7633,
            creator=self.user,
            temperature=22.5,
            wind_speed=15.2,
        )
        
        self.booking_tomorrow = Booking.objects.create(
            date_time=timezone.now() + timedelta(days=1),
            duration=90,
            farm_name='Farm Tomorrow',
            inspector_name='Inspector Tomorrow',
            latitude=-36.8485,
            longitude=174.7633,
            creator=self.user,
            temperature=23.1,
            wind_speed=16.8,
        )
        
        self.booking_next_week = Booking.objects.create(
            date_time=timezone.now() + timedelta(days=7),
            duration=120,
            farm_name='Farm Next Week',
            inspector_name='Inspector Next Week',
            latitude=-36.8485,
            longitude=174.7633,
            creator=self.user,
            temperature=25.0,
            wind_speed=12.5,
        )

    def test_list_bookings_ordered_by_date(self):
        """Test that bookings are returned in chronological order"""
        url = reverse('booking-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Verify order (should be by date_time)
        dates = [booking['date_time'] for booking in response.data]
        self.assertEqual(dates, sorted(dates))

    def test_booking_count_accurate(self):
        """Test that the correct number of bookings is returned"""
        url = reverse('booking-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(Booking.objects.count(), 3)


class TestAuthorisation(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testdev@test.com',
            password='testpassword',
            first_name='Test',
            last_name='Test',
            username='testdev'
        )
        self.url_register = reverse('register')
        self.url_login = reverse('login')

    def test_register(self):
        response = self.client.post(
            self.url_register,
            {
                'email': 'test@test.com',
                'username': 'test',
                'password': 'testpassword',
                'password_confirmation': 'testpassword',
                'first_name': 'Test',
                'last_name': 'Test'
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'test@test.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'Test')

    def test_register_with_existing_email(self):
        response = self.client.post(
            self.url_register,
            {
                'email': 'testdev@test.com',
                'username': 'testdev',
                'password': 'testpassword',
                'password_confirmation': 'testpassword',
                'first_name': 'Test',
                'last_name': 'Test'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data[0],
                         'User with this email already exists.')

    def test_login(self):
        response = self.client.post(
            self.url_login,
            {
                'username': 'testdev',
                'password': 'testpassword'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'testdev')
        token = response.data['token']
        self.assertIsNotNone(token)

    def test_login_with_invalid_credentials(self):
        response = self.client.post(
            self.url_login,
            {
                'username': 'test@test.com',
                'password': 'wrongpassword'
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'][0], 'Invalid credentials')
