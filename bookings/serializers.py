from datetime import datetime

import requests
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Booking, Notes


class NotesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notes
        fields = ['id', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Booking model.
    """
    notes = NotesSerializer(many=True, required=False)

    class Meta:
        model = Booking
        fields = [
            'id',
            'date_time',
            'duration',
            'farm_name',
            'inspector_name',
            'latitude',
            'longitude',
            'notes',
            'temperature',
            'wind_speed',
            'creator',
        ]
        read_only_fields = ['id', 'creator', 'temperature', 'wind_speed']

    def validate_date_time(self, value: datetime) -> datetime:
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

    def create(self, validated_data):
        notes_data = validated_data.pop('notes', [])
        user = self.context['request'].user
        validated_data['creator'] = user

        # Create the booking
        booking = super().create(validated_data)

        # Create notes for the booking (only if notes_data is not empty)
        if notes_data:
            for note_data in notes_data:
                Notes.objects.create(
                    content=note_data['content'],
                    booking=booking
                )

        return booking

    def update(self, instance, validated_data):
        notes_data = validated_data.pop('notes', None)
        user = self.context['request'].user
        validated_data['creator'] = user

        # Update the booking
        booking = super().update(instance, validated_data)

        # Handle notes update if provided
        if notes_data is not None:
            # Delete existing notes
            booking.notes.all().delete()

            # Create new notes (only if notes_data is not empty)
            if notes_data:
                for note_data in notes_data:
                    Notes.objects.create(
                        content=note_data['content'],
                        booking=booking
                    )

        return booking


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password_confirmation = serializers.CharField(write_only=True)

    def validate_password(self, value) -> str:
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long")
        return value

    def validate_password_confirmation(self, value) -> str:
        if value != self.initial_data.get('password'):
            raise serializers.ValidationError(
                "Password confirmation does not match")
        return value

    def validate(self, data) -> dict:
        self.validate_password_confirmation(data['password_confirmation'])
        self.validate_password(data['password'])
        data.pop('password_confirmation')
        return data

    def create(self, validated_data) -> User:
        if User.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError(
                "User with this email already exists."
            )

        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            password=validated_data['password'],
            username=validated_data['username'],
        )

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data) -> dict:
        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        data['user'] = user
        return data
