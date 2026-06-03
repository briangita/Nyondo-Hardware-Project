from django.db import models

# Create your models here.

class Vehicle(models.Model):
    vehicle_name = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=50, unique=True)
    vehicle_type = models.CharField(max_length=50, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    driver_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.vehicle_name} - {self.registration_number}"