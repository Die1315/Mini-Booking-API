from datetime import datetime, timedelta

import requests
from django.conf import settings
from requests import Request
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Booking
from .serializers import BookingSerializer


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def _round_down_to_nearest_hour(
        self, booking_datetime: datetime,
    ) -> datetime:
        """
        Round down the datetime to the nearest hour.
        """
        if booking_datetime.minute > 30:
            booking_datetime += timedelta(hours=1)

        booking_datetime = booking_datetime.replace(
            minute=0, second=0, microsecond=0
        )
        return booking_datetime

    def _fetch_weather(self, serializer_data: Request) -> Response:
        """
        Método de utilidad para obtener el clima y actualizar los datos del serializador.
        """
        latitude = serializer_data.get('latitude')
        longitude = serializer_data.get('longitude')
        booking_datetime = serializer_data.get('date_time')

        booking_datetime = self._round_down_to_nearest_hour(booking_datetime)

        url = f"{settings.WEATHER_API_URL}?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,windspeed_10m&start_date={booking_datetime.date()}&end_date={booking_datetime.date()}"  # noqa

        try:
            weather_response = requests.get(url)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            hourly_data = weather_data.get('hourly', {})
            times = hourly_data.get('time', [])
            temperatures = hourly_data.get('temperature_2m', [])
            wind_speeds = hourly_data.get('windspeed_10m', [])

            temperature = None
            wind_speed = None

            for i, time_str in enumerate(times):
                forecast_time = datetime.fromisoformat(
                    time_str
                ).replace(tzinfo=None)
                if forecast_time == booking_datetime.replace(tzinfo=None):
                    temperature = temperatures[i]
                    wind_speed = wind_speeds[i]
                    break

            serializer_data['temperature'] = temperature
            serializer_data['wind_speed'] = wind_speed

        except requests.RequestException as e:
            print(f"Error fetching weather data: {e}")

        return serializer_data

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self._fetch_weather(serializer.validated_data)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )

        serializer.is_valid(raise_exception=True)

        if 'date_time' in serializer.validated_data or 'latitude' in serializer.validated_data or 'longitude' in serializer.validated_data:
            self._fetch_weather(serializer.validated_data)

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
            
        return Response(serializer.data)
