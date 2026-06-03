from django.db import models

# Create your models here.
class OperatingExpense(models.Model):

    EXPENSE_CATEGORIES = [
        ("rent", "Rent"),
        ("electricity", "Electricity"),
        ("water", "Water"),
        ("internet", "Internet"),
        ("fuel", "Fuel"),
        ("vehicle_maintenance", "Vehicle Maintenance"),
        ("staff_meals", "Staff Meals"),
        ("salaries_wages", "Salaries/Wages"),
        ("stationery", "Stationery"),
        ("repairs", "Repairs"),
        ("security", "Security"),
        ("bank_charges", "Bank Charges"),
        ("other", "Other"),
    ]

    category = models.CharField(max_length=50,choices=EXPENSE_CATEGORIES)
    invoice_number = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    expense_date = models.DateField()
    paid_to = models.CharField(max_length=150,blank=True)
    reference_number = models.CharField(max_length=100,blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"{self.get_category_display()} - {self.amount}"