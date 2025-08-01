from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Booking(models.Model):
    """
    Booking is the main model for a booking.
    """
    date_time = models.DateTimeField(default=timezone.now)
    duration = models.IntegerField(default=1)

    farm_name = models.CharField(max_length=255)
    inspector_name = models.CharField(max_length=255)

    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    temperature = models.DecimalField(max_digits=5, decimal_places=2)
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.date_time} - {self.farm_name}"


class Notes(models.Model):
    """
    Notes are used to add additional information to a booking.
    """
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name='notes'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.booking.farm_name} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}" # noqa
            )

class CustomUser(AbstractUser):
    """
    Custom user model.
    """
    pass