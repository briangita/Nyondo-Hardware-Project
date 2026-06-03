from django.db import models
from decimal import Decimal
from transport.models import Vehicle
from stock.models import Product
# Create your models here.


class Sales(models.Model):
    CUSTOMER_TYPES = [
        ("retail", "Retail"),
        ("wholesale", "Wholesale"),
    ]

    PAYMENT_TYPES = [
        ("cash", "Cash"),
        ("mobilemoney", "Mobile Money"),
        ("banktransfer", "Bank Transfer"),
        ("cheque", "Cheque"),
        ("salaryscheme", "Salary Scheme"),
    ]

    customer_name = models.CharField(max_length=150)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default="retail")
    customer_paid = models.BooleanField(default=False)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, blank=True)
    sale_date = models.DateTimeField(auto_now_add=True)

    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    output_vat = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    transport_required = models.BooleanField(default=False)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    transport_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    assigned_vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)

    def update_totals(self):
        self.subtotal = sum(
            (item.subtotal for item in self.items.all()),
            Decimal("0.00")
        )

        self.output_vat = sum(
            (item.output_vat for item in self.items.all()),
            Decimal("0.00")
        )

        goods_total = sum(
            (item.total_price for item in self.items.all()),
            Decimal("0.00")
        )

        distance_km = Decimal(str(self.distance_km or "0"))

        if self.transport_required:
            if distance_km <= Decimal("10") and goods_total >= Decimal("500000"):
                self.transport_fee = Decimal("0.00")
            else:
                self.transport_fee = Decimal("30000.00")
        else:
            self.transport_fee = Decimal("0.00")

        self.total_price = goods_total + self.transport_fee
        self.save()

    def __str__(self):
        return f"{self.customer_name} - INV-{self.id}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sales, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    selling_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    vat_applicable = models.BooleanField(default=False)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    output_vat = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    

    def save(self, *args, **kwargs):
        if self.sale.customer_type == "wholesale":
            self.selling_price = self.product.wholesale_price
        else:
            self.selling_price = self.product.retail_price

        self.subtotal = self.selling_price * self.quantity
        self.output_vat = self.subtotal * Decimal("0.18") if self.vat_applicable else Decimal("0.00")
        self.total_price = self.subtotal

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity}" # Display product name and quantity for better readability
    

