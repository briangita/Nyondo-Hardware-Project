from django.shortcuts import render, redirect, get_object_or_404
from sales.models import Product, Sales, SaleItem
from .models import SchemeCustomer, SchemePayment, SchemeGoodsPickup
from django.db.models import Sum
from stock.models import StockReceipt
from django.contrib import messages # For user feedback messages
import re # For regex validation in the data validation views
from decimal import Decimal ,InvalidOperation # For accurate financial calculations
from django.db import transaction # For atomic transactions when recording pickups
from users.decorators import admin_required, admin_or_sales_attendant_required,admin_or_accounts_or_sales_attendant_required
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required
@admin_or_sales_attendant_required
def scheme_customer_list(request):
    customers = SchemeCustomer.objects.all().order_by("-date_registered")
    return render(request, "scheme_customer_list.html", {"customers": customers})


@login_required
@admin_or_sales_attendant_required
def register_scheme_customer(request):
    if request.method == "POST":
        form_data = request.POST
        errors = {}

        full_name = form_data.get("full_name", "").strip()
        nin_number = form_data.get("nin_number", "").strip().upper()
        phone_number = form_data.get("phone_number", "").strip()
        address = form_data.get("address", "").strip()
        occupation = form_data.get("occupation", "").strip()
        employer_name = form_data.get("employer_name", "").strip()

        nin_pattern = r"^(CM|CF)[0-9]{10}[A-Z]{2}$"
        phone_pattern = r"^07[0-9]{8}$"

        if not full_name:
            errors["full_name"] = "Full name is required."

        if not nin_number:
            errors["nin"] = "NIN number is required."
        elif not re.match(nin_pattern, nin_number):
            errors["nin"] = "Invalid NIN format. Use format like CF1234567890GH."
        elif SchemeCustomer.objects.filter(nin_number=nin_number).exists():
            errors["nin"] = "A customer with this NIN already exists."

        if not phone_number:
            errors["phone"] = "Phone number is required."
        elif not re.match(phone_pattern, phone_number):
            errors["phone"] = "Invalid phone number. Use format like 0781234567."

        if not address:
            errors["address"] = "Address is required."

        if not occupation:
            errors["occupation"] = "Occupation is required."

        if errors:
            return render(request, "register_scheme_customer.html", {
                "errors": errors,
                "form_data": form_data,
            })

        SchemeCustomer.objects.create(
            full_name=full_name,
            nin_number=nin_number,
            phone_number=phone_number,
            address=address,
            occupation=occupation,
            employer_name=employer_name,
        )

        messages.success(request, "Scheme customer registered successfully.")
        return redirect("scheme_customer_list")

    return render(request, "register_scheme_customer.html", {
        "errors": {},
        "form_data": {},
    })


@login_required
@admin_or_sales_attendant_required
def record_scheme_payment(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)

    if request.method == "POST":
        payment = SchemePayment.objects.create(
            customer=customer,
            amount_paid=request.POST.get("amount_paid"),
            notes=request.POST.get("notes"),
        )

        return redirect("temporary_receipt", payment_id=payment.id)

    return render(request, "record_scheme_payment.html", {"customer": customer})

@login_required
@admin_or_sales_attendant_required
def temporary_receipt(request, payment_id):
    payment = get_object_or_404(SchemePayment, id=payment_id)
    return render(request, "temporary_receipt.html", {"payment": payment})


@login_required
@admin_or_sales_attendant_required
def customer_scheme_detail(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)
    payments = SchemePayment.objects.filter(customer=customer)
    pickups = SchemeGoodsPickup.objects.filter(customer=customer)

    total_paid = sum(payment.amount_paid for payment in payments)
    total_goods_value = sum(
        pickup.linked_sale.total_price
        for pickup in pickups
        if pickup.linked_sale
    )

    balance = total_paid - total_goods_value

    return render(request, "customer_scheme_detail.html", {
        "customer": customer,
        "payments": payments,
        "pickups": pickups,
        "total_paid": total_paid,
        "total_goods_value": total_goods_value,
        "balance": balance,
    })

@login_required
@admin_or_sales_attendant_required
def scheme_dashboard(request):
    total_customers = SchemeCustomer.objects.count()

    total_deposits = SchemePayment.objects.aggregate(
        total=Sum("amount_paid")
    )["total"] or Decimal("0.00")

    pickups = SchemeGoodsPickup.objects.select_related("linked_sale")

    goods_value = Decimal("0.00")

    for pickup in pickups:
        if pickup.linked_sale:
            goods_value += pickup.linked_sale.total_price

    scheme_balance = total_deposits - goods_value

    return render(request, "scheme_dashboard.html", {
        "total_customers": total_customers,
        "total_deposits": total_deposits,
        "goods_value": goods_value,
        "scheme_balance": scheme_balance,
    })
    
@login_required
@admin_or_accounts_or_sales_attendant_required    
def scheme_report(request):
    customers = SchemeCustomer.objects.all().order_by(
        "full_name"
    )

    report_data = []

    total_deposits_all = Decimal("0.00")
    total_goods_all = Decimal("0.00")
    total_balance_all = Decimal("0.00")

    for customer in customers:

        total_deposits = SchemePayment.objects.filter(
            customer=customer
        ).aggregate(
            total=Sum("amount_paid")
        )["total"] or Decimal("0.00")

        pickups = SchemeGoodsPickup.objects.filter(
            customer=customer
        ).select_related("linked_sale")

        goods_value = Decimal("0.00")

        for pickup in pickups:

            if pickup.linked_sale:
                goods_value += pickup.linked_sale.total_price

        balance = total_deposits - goods_value

        total_deposits_all += total_deposits
        total_goods_all += goods_value
        total_balance_all += balance

        report_data.append({
            "customer": customer,
            "total_deposits": total_deposits,
            "goods_value": goods_value,
            "balance": balance,
        })

    return render(
        request,
        "scheme_report.html",
        {
            "report_data": report_data,
            "total_deposits_all": total_deposits_all,
            "total_goods_all": total_goods_all,
            "total_balance_all": total_balance_all,
        }
    )

def get_scheme_customer_balance(customer):
    payments = SchemePayment.objects.filter(customer=customer)

    pickups = SchemeGoodsPickup.objects.filter(
        customer=customer
    ).select_related("linked_sale")

    total_paid = payments.aggregate(
        total=Sum("amount_paid")
    )["total"] or Decimal("0.00")

    total_goods_value = Decimal("0.00")

    for pickup in pickups:
        if pickup.linked_sale:
            total_goods_value += pickup.linked_sale.total_price

    return total_paid - total_goods_value

@login_required
@admin_or_sales_attendant_required
def scheme_goods_pickup(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)

    products = Product.objects.filter(
        category_name__category_name__in=[
            "Cement",
            "Iron Sheets",
            "Iron Bars"
        ]
    )

    balance = get_scheme_customer_balance(customer)

    if request.method == "POST":
        try:
            product = get_object_or_404(Product, id=request.POST.get("product"))
            quantity = int(request.POST.get("quantity") or 0)

            if quantity <= 0:
                raise ValueError("Quantity must be greater than zero.")

            # Stock calculation
            total_received = StockReceipt.objects.filter(product=product)\
                .aggregate(total=Sum("quantity_received"))["total"] or 0

            total_sold = SaleItem.objects.filter(product=product)\
                .aggregate(total=Sum("quantity"))["total"] or 0

            available_stock = total_received - total_sold

            if quantity > available_stock:
                raise ValueError(f"Not enough stock. Available stock is {available_stock}.")

            # Pricing
            vat_applicable = request.POST.get("vat_applicable") == "on"
            transport_required = request.POST.get("transport_required") == "on"
            distance_km = Decimal(request.POST.get("distance_km") or "0")

            selling_price = product.retail_price
            subtotal = selling_price * quantity
            output_vat = subtotal * Decimal("0.18") if vat_applicable else Decimal("0.00")
            goods_total = subtotal + output_vat

            # Transport logic
            if transport_required:
                if distance_km <= Decimal("10") and goods_total >= Decimal("500000"):
                    transport_fee = Decimal("0.00")
                else:
                    transport_fee = Decimal("30000.00")
            else:
                transport_fee = Decimal("0.00")

            estimated_total = goods_total + transport_fee

            if estimated_total > balance:
                raise ValueError(
                    f"Insufficient balance. Available: {balance:,.2f}, "
                    f"Required: {estimated_total:,.2f}"
                )

            # Transaction
            with transaction.atomic():
                sale = Sales.objects.create(
                    customer_name=customer.full_name,
                    customer_type="retail",
                    customer_paid=True,
                    payment_type="salaryscheme",
                    transport_required=transport_required,
                    distance_km=distance_km
                )

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    vat_applicable=vat_applicable
                )

                sale.update_totals()

                SchemeGoodsPickup.objects.create(
                    customer=customer,
                    product=product,
                    quantity_taken=quantity,
                    linked_sale=sale
                )

            return redirect("invoice", sale_id=sale.id)

        except (ValueError, InvalidOperation) as e:
            return render(request, "scheme_goods_pickup.html", {
                "customer": customer,
                "products": products,
                "balance": balance,
                "error": str(e)
            })

    return render(request, "scheme_goods_pickup.html", {
        "customer": customer,
        "products": products,
        "balance": balance,
    })
    
@login_required
@admin_or_accounts_or_sales_attendant_required    
def customer_statement(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)

    payments = SchemePayment.objects.filter(customer=customer)
    pickups = SchemeGoodsPickup.objects.filter(customer=customer).select_related("linked_sale")

    transactions = []

    # Add payments (CREDIT)
    for payment in payments:
        transactions.append({
            "date": payment.payment_date,
            "type": "Deposit",
            "reference": f"PAY-{payment.id}",
            "debit": Decimal("0.00"),
            "credit": payment.amount_paid,
        })

    # Add pickups (DEBIT)
    for pickup in pickups:
        if pickup.linked_sale:
            transactions.append({
                "date": pickup.pickup_date,
                "type": "Goods Pickup",
                "reference": f"INV-{pickup.linked_sale.id}",
                "debit": pickup.linked_sale.total_price,
                "credit": Decimal("0.00"),
            })

    # Sort by date
    transactions = sorted(transactions, key=lambda x: x["date"])

    # Running balance
    balance = Decimal("0.00")

    for tx in transactions:
        balance += tx["credit"]
        balance -= tx["debit"]
        tx["balance"] = balance

    return render(request, "customer_statement.html", {
        "customer": customer,
        "transactions": transactions,
        "final_balance": balance,
    })