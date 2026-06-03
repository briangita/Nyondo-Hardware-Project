from django.urls import path
from . import views

urlpatterns = [
    path("vehicles/", views.vehicle_list, name="vehicle_list"),
    path("vehicles/create/", views.create_vehicle, name="create_vehicle"),
    path("vehicles/<int:vehicle_id>/edit/", views.edit_vehicle, name="edit_vehicle"),
]