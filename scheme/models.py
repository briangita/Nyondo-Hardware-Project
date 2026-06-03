from django.db import models
from sales.models import Product, Sales
from decimal import Decimal
from django.db.models import Sum

# Create your models here.
class SchemeCustomer(models.Model):
    full_name = models.CharField(max_length=150)
    nin_number = models.CharField(max_length=30, unique=True)
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    occupation = models.CharField(max_length=100, default="Salary Earner")
    employer_name = models.CharField(max_length=150, blank=True)
    date_registered = models.DateTimeField(auto_now_add=True)
    
    def total_deposits(self):
        return self.schemepayment_set.aggregate(
            total=Sum("amount_paid")
        )["total"] or Decimal("0.00")

    def total_goods_taken(self):
        pickups = self.schemegoodspickup_set.select_related(
            "linked_sale"
        )

        total = Decimal("0.00")

        for pickup in pickups:
            if pickup.linked_sale:
                total += pickup.linked_sale.total_price

        return total

    def available_balance(self):
        return self.total_deposits() - self.total_goods_taken()

    def __str__(self):
        return self.full_name


class SchemePayment(models.Model):
    customer = models.ForeignKey(SchemeCustomer, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self): # This method defines how the SchemePayment object will be represented as a string, which is useful for admin interfaces and debugging. It returns a string that includes the customer's full name and the amount paid.
        return f"{self.customer.full_name} - {self.amount_paid}"# Create your models here.


class SchemeGoodsPickup(models.Model):
    customer = models.ForeignKey(SchemeCustomer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_taken = models.PositiveIntegerField()
    linked_sale = models.ForeignKey(Sales, on_delete=models.SET_NULL, null=True, blank=True)
    pickup_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.full_name} - {self.product.product_name}"