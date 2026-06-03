from decimal import Decimal
from django.db import models



class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.category_name

class Product(models.Model):
    category_name = models.ForeignKey(Category, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=100)
    cost_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    retail_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    wholesale_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    description = models.TextField()

    def __str__(self):
        return self.product_name

class StockReceipt(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier_name = models.CharField(max_length=100)
    supplier_invoice_number = models.CharField(max_length=100,blank=True)
    quantity_received = models.PositiveIntegerField()

    unit_cost = models.DecimalField(max_digits=15, decimal_places=2)
    retail_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    wholesale_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    vat_applicable = models.BooleanField(default=False)
    input_vat = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount_due = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    supplier_paid = models.BooleanField(default=False)
    date_received = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity_received * self.unit_cost
        self.input_vat = self.subtotal * Decimal("0.18") if self.vat_applicable else Decimal("0.00")
        self.total_amount_due = self.subtotal

        self.product.cost_price = self.unit_cost
        self.product.retail_price = self.retail_price # Update retail price from stock receipt
        self.product.wholesale_price = self.wholesale_price
        self.product.save()

        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.product_name} - {self.quantity_received}"