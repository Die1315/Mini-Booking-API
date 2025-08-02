from datetime import datetime, timedelta

import requests

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from django.shortcuts import render
from requests import Request
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking
from .serializers import BookingSerializer, LoginSerializer, RegisterSerializer


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

        if (
            'date_time' in serializer.validated_data or
            'latitude' in serializer.validated_data or
            'longitude' in serializer.validated_data
        ):
            self._fetch_weather(serializer.validated_data)

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

# Simple authentication


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "http://localhost:8000/google/callback/"


def google_callback(request):
    code = request.GET.get('code')
    if code:
        return render(request, 'callback.html', {'code': code})
    return render(request, 'callback.html', {'code': 'Code not found.'})
