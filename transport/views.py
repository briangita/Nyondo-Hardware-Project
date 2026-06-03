from django.shortcuts import render, redirect, get_object_or_404
from .models import Vehicle
from django.contrib import messages
from users.decorators import admin_required
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
@admin_required
def vehicle_list(request):
    vehicles = Vehicle.objects.all().order_by("vehicle_name")

    return render(request, "vehicle_list.html", {
        "vehicles": vehicles
    })
    
@login_required
@admin_required
def create_vehicle(request):
    if request.method == "POST":
        vehicle_name = request.POST.get("vehicle_name")
        registration_number = request.POST.get("registration_number")
        vehicle_type = request.POST.get("vehicle_type")
        driver_name = request.POST.get("driver_name")
        driver_phone = request.POST.get("driver_phone")
        
        if not vehicle_name or not registration_number or not vehicle_type:
            messages.error(request, "Please fill in all required fields.")
            return render(request, "create_vehicle.html")

        Vehicle.objects.create(
            vehicle_name=vehicle_name,
            registration_number=registration_number,
            vehicle_type=vehicle_type,
            driver_name=driver_name,
            driver_phone=driver_phone,
        )

        messages.success(request, "Vehicle added successfully.")

        return redirect("vehicle_list")

    return render(request, "create_vehicle.html")

@login_required
@admin_required
def edit_vehicle(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == "POST":
        vehicle.vehicle_name = request.POST.get("vehicle_name")
        vehicle.registration_number = request.POST.get("registration_number")
        vehicle.vehicle_type = request.POST.get("vehicle_type")
        vehicle.driver_name = request.POST.get("driver_name")
        vehicle.driver_phone = request.POST.get("driver_phone")
        vehicle.is_active = request.POST.get("is_active") == "on"
        
        if not vehicle.vehicle_name or not vehicle.registration_number or not vehicle.vehicle_type:
            messages.error(request, "Please fill in all required fields.")
            return render(request, "edit_vehicle.html", {
                "vehicle": vehicle
            })

        vehicle.save()

        messages.success(request, "Vehicle updated successfully.")

        return redirect("vehicle_list")

    return render(request, "edit_vehicle.html", {
        "vehicle": vehicle
    })