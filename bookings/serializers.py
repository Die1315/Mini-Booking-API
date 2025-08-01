from datetime import date

import requests
from django.conf import settings
from rest_framework import serializers

from .models import Booking, Notes


class NotesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notes
        fields = ['__all__']
        read_only_fields = ['id', 'created_at']


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Booking model.
    """
    notes = NotesSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = ['__all__']
        read_only_fields = ['id']

    def validate_date(self, value: date) -> date:
        '''
        Validate if the booking date is not a public holiday in NZ.
        and if the date is in the future.
        '''
        year = value.year
        country = 'NZ'
        url = f'{settings.PUBLIC_HOLIDAYS_API_URL}/{year}/{country}'

        try:
            response = requests.get(url)
            response.raise_for_status()
            public_holidays = response.json()
        except requests.exceptions.RequestException as e:
            raise serializers.ValidationError(
                f'Error fetching public holidays: {e}'
            )

        public_holidays_dates = [
            holiday['date'] for holiday in public_holidays
        ]

        booking_date = value.strftime("%Y-%m-%d")

        if booking_date in public_holidays_dates:
            raise serializers.ValidationError(
                'Booking date cannot be a public holiday.'
            )

        return value



