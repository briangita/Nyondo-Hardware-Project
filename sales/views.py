from django.shortcuts import render, redirect, get_object_or_404
from .models import Sales, SaleItem, Vehicle
from django.db import IntegrityError #
from stock.models import StockReceipt
from django.db.models import Sum # For calculating totals in views
from django.http import HttpResponse # For Excel export
from openpyxl import Workbook # For Excel export
from django.contrib.auth.decorators import login_required # For protecting views (remember to add protection of the views)
from decimal import Decimal, InvalidOperation
from django.db.models.functions import TruncDate, TruncMonth # For sales dashboard date grouping
from stock.models import Product 
from django.contrib import messages # For user feedback on edit sale
from users.decorators import admin_required, sales_attendant_required, admin_or_accounts_or_sales_attendant_required, admin_or_sales_attendant_required

# Create your views here
@login_required
@admin_or_sales_attendant_required
def sales_list(request):
    sales = Sales.objects.all().order_by("-sale_date")

    total_output_vat = sales.aggregate(total=Sum("output_vat"))["total"] or 0
    total_sales_value = sales.aggregate(total=Sum("total_price"))["total"] or 0
    total_transport_fee = sales.aggregate(total=Sum("transport_fee"))["total"] or 0

    return render(request, "sales_list.html", {
        "sales": sales,
        "total_output_vat": total_output_vat,
        "total_sales_value": total_sales_value,
        "total_transport_fee": total_transport_fee
    })

@login_required
@admin_or_sales_attendant_required    
def create_sale(request):
    products = Product.objects.all()
    vehicles = Vehicle.objects.filter(is_active=True)

    if request.method == "POST":
        errors = {}
        data = request.POST

        try:
            customer_paid = data.get("customer_paid") == "on"
            customer_name = data.get("customer_name", "").strip()
            customer_type = data.get("customer_type", "")
            product_ids = data.getlist("product")
            quantities = data.getlist("quantity")
            payment_type = data.get("payment_type") if customer_paid else ""
            transport_required = data.get("transport_required") == "on"

            distance_km = Decimal(data.get("distance_km") or "0")
            assigned_vehicle = None

            if not customer_name:
                errors["customer_name"] = "Customer name is required."

            if not customer_type:
                errors["customer_type"] = "Customer type is required."

            if customer_paid and not payment_type:
                errors["payment_type"] = "Payment type is required."

            if not any(q.strip() for q in quantities):
                errors["products"] = "At least one product is required."

            if transport_required:
                if distance_km <= 0:
                    errors["distance_km"] = "Distance must be greater than zero."

                assigned_vehicle_id = data.get("assigned_vehicle")

                if not assigned_vehicle_id:
                    errors["assigned_vehicle"] = "Vehicle is required."
                else:
                    assigned_vehicle = Vehicle.objects.filter(
                        id=assigned_vehicle_id,
                        is_active=True
                    ).first()

                    if not assigned_vehicle:
                        errors["assigned_vehicle"] = "Invalid vehicle selected."

            for index, product_id in enumerate(product_ids):
                qty = quantities[index].strip()

                if not product_id and not qty:
                    continue

                if not product_id:
                    errors[f"product_{index}"] = "Select a product."

                if not qty:
                    errors[f"quantity_{index}"] = "Enter quantity."
                    continue

                try:
                    quantity = int(qty)
                    if quantity <= 0:
                        errors[f"quantity_{index}"] = "Must be greater than zero."
                        continue
                except:
                    errors[f"quantity_{index}"] = "Invalid number."
                    continue

                product = Product.objects.filter(id=product_id).first()
                if not product:
                    errors[f"product_{index}"] = "Invalid product."
                    continue

                total_received = StockReceipt.objects.filter(
                    product=product
                ).aggregate(total=Sum("quantity_received"))["total"] or 0

                total_sold = SaleItem.objects.filter(
                    product=product
                ).aggregate(total=Sum("quantity"))["total"] or 0

                available_stock = total_received - total_sold

                if quantity > available_stock:
                    errors[f"quantity_{index}"] = f"Only {available_stock} in stock."

            if errors:
                return render(request, "create_sale.html", {
                    "products": products,
                    "vehicles": vehicles,
                    "errors": errors,
                    "data": data
                })

            sale = Sales.objects.create(
                customer_name=customer_name,
                customer_type=customer_type,
                customer_paid=customer_paid,
                payment_type=payment_type,
                transport_required=transport_required,
                distance_km=distance_km,
                assigned_vehicle=assigned_vehicle,
            )

            for index, product_id in enumerate(product_ids):
                if not product_id:
                    continue

                quantity = int(quantities[index])

                SaleItem.objects.create(
                    sale=sale,
                    product_id=product_id,
                    quantity=quantity,
                    vat_applicable=f"vat_applicable_{index}" in data
                )

            sale.update_totals()

            return redirect("invoice", sale_id=sale.id)

        except (InvalidOperation, ValueError):
            return render(request, "create_sale.html", {
                "products": products,
                "vehicles": vehicles,
                "errors": {"general": "Invalid input values."},
                "data": data
            })

    return render(request, "create_sale.html", {
        "products": products,
        "vehicles": vehicles
    })

@login_required
@admin_or_sales_attendant_required
def invoice(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)

    return render(request, "invoice.html", {
        "sale": sale
    })

@login_required
@admin_or_sales_attendant_required
def edit_sale(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    products = Product.objects.all()
    vehicles = Vehicle.objects.filter(is_active=True)

    if request.method == "POST":
        errors = {}
        data = request.POST

        try:
            customer_name = data.get("customer_name", "").strip()
            customer_type = data.get("customer_type")
            customer_paid = data.get("customer_paid") == "on"
            payment_type = data.get("payment_type") if customer_paid else ""

            product_ids = data.getlist("product")
            quantities = data.getlist("quantity")

            transport_required = data.get("transport_required") == "on"
            distance_km = Decimal(data.get("distance_km") or "0")
            assigned_vehicle_id = data.get("assigned_vehicle")

            assigned_vehicle = None

            if not customer_name:
                errors["customer_name"] = "Customer name is required."

            if not customer_type:
                errors["customer_type"] = "Customer type is required."

            if customer_paid and not payment_type:
                errors["payment_type"] = "Payment type is required."

            if not any(q.strip() for q in quantities):
                errors["products"] = "At least one product is required."

            if transport_required:
                if distance_km <= 0:
                    errors["distance_km"] = "Distance must be greater than zero."

                if not assigned_vehicle_id:
                    errors["assigned_vehicle"] = "Assign a vehicle."

                else:
                    assigned_vehicle = get_object_or_404(
                        Vehicle,
                        id=assigned_vehicle_id,
                        is_active=True
                    )

            if errors:
                return render(request, "edit_sale.html", {
                    "sale": sale,
                    "products": products,
                    "vehicles": vehicles,
                    "errors": errors,
                    "data": data
                })

            sale.customer_name = customer_name
            sale.customer_type = customer_type
            sale.customer_paid = customer_paid
            sale.payment_type = payment_type
            sale.transport_required = transport_required
            sale.distance_km = distance_km
            sale.assigned_vehicle = assigned_vehicle
            sale.save()

            sale.items.all().delete()

            for index, product_id in enumerate(product_ids):
                if not product_id:
                    continue

                product = get_object_or_404(Product, id=product_id)
                quantity = int(quantities[index])

                total_received = StockReceipt.objects.filter(
                    product=product
                ).aggregate(total=Sum("quantity_received"))["total"] or 0

                total_sold = SaleItem.objects.filter(
                    product=product
                ).aggregate(total=Sum("quantity"))["total"] or 0

                available_stock = total_received - total_sold

                if quantity > available_stock:
                    errors[f"quantity_{index}"] = f"Only {available_stock} available."

            if errors:
                return render(request, "edit_sale.html", {
                    "sale": sale,
                    "products": products,
                    "vehicles": vehicles,
                    "errors": errors,
                    "data": data
                })

            for index, product_id in enumerate(product_ids):
                if not product_id:
                    continue

                SaleItem.objects.create(
                    sale=sale,
                    product_id=product_id,
                    quantity=int(quantities[index]),
                    vat_applicable=f"vat_applicable_{index}" in data
                )

            sale.update_totals()

            messages.success(request, "Sale updated successfully.")
            return redirect("invoice", sale_id=sale.id)

        except (ValueError, InvalidOperation):
            return render(request, "edit_sale.html", {
                "sale": sale,
                "products": products,
                "vehicles": vehicles,
                "errors": {"general": "Invalid numbers entered."},
                "data": data
            })

    return render(request, "edit_sale.html", {
        "sale": sale,
        "products": products,
        "vehicles": vehicles
    })
    
@login_required
@admin_required
def delete_sale(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)

    if request.method == "POST":
        sale.delete()
        return redirect("sales_list")

    return render(request, "delete_sale.html", {
        "sale": sale
    })

@login_required
@admin_or_accounts_or_sales_attendant_required
def sales_report(request):
    sales = Sales.objects.all().order_by("-sale_date")

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date:
        sales = sales.filter(sale_date__date__gte=start_date)

    if end_date:
        sales = sales.filter(sale_date__date__lte=end_date)

    sale_items = SaleItem.objects.filter(sale__in=sales)

    total_sales_amount = sales.aggregate(
        total=Sum("total_price")
    )["total"] or 0

    total_quantity_sold = sale_items.aggregate(
        total=Sum("quantity")
    )["total"] or 0

    total_output_vat = sale_items.aggregate(
        total=Sum("output_vat")
    )["total"] or 0

    return render(request, "sales_report.html", {
        "sales": sales,
        "sale_items": sale_items,
        "start_date": start_date,
        "end_date": end_date,
        "total_sales_amount": total_sales_amount,
        "total_quantity_sold": total_quantity_sold,
        "total_output_vat": total_output_vat,
    })

@login_required
@admin_or_accounts_or_sales_attendant_required
def export_sales_report_excel(request):
    sales = Sales.objects.all().order_by("-sale_date")

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date and start_date != "None":
        sales = sales.filter(sale_date__date__gte=start_date)

    if end_date and end_date != "None":
        sales = sales.filter(sale_date__date__lte=end_date)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Sales Report"

    worksheet.append([
        "Invoice",
        "Customer",
        "Customer Type",
        "Product",
        "Category",
        "Selling Price",
        "Quantity",
        "Subtotal",
        "Output VAT",
        "Item Total",
        "Invoice Total",
        "Paid?",
        "Payment Type",
        "Sale Date"
    ])

    for sale in sales:
        for item in sale.items.all():
            worksheet.append([
                f"INV-{sale.id}",
                sale.customer_name,
                sale.get_customer_type_display(),
                item.product.product_name,
                item.product.category_name.category_name,
                item.selling_price,
                item.quantity,
                item.subtotal,
                item.output_vat,
                item.total_price,
                sale.total_price,
                "Paid" if sale.customer_paid else "Not Paid",
                sale.get_payment_type_display() if sale.customer_paid else "",
                sale.sale_date.strftime("%Y-%m-%d %H:%M"),
            ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="sales_report.xlsx"'

    workbook.save(response)
    return response

@login_required
@admin_or_sales_attendant_required
def sales_dashboard(request):

    # KPIs
    total_sales = Sales.objects.aggregate(
        total=Sum("total_price")
    )["total"] or Decimal("0.00")

    unpaid_sales = Sales.objects.filter(
        customer_paid=False
    ).aggregate(
        total=Sum("total_price")
    )["total"] or Decimal("0.00")

    output_vat = Sales.objects.aggregate(
        total=Sum("output_vat")
    )["total"] or Decimal("0.00")

    total_invoices = Sales.objects.count()

    unpaid_count = Sales.objects.filter(customer_paid=False).count()

    average_sale = total_sales / total_invoices if total_invoices else Decimal("0.00")

    # Daily Sales: the 7 most recent trading days, newest first
    daily_sales = list(
        Sales.objects
        .annotate(day=TruncDate("sale_date"))
        .values("day")
        .annotate(total=Sum("total_price"))
        .order_by("-day")[:7]
    )

    max_day = max([d["total"] for d in daily_sales], default=0) or 1

    for item in daily_sales:
        item["percentage"] = item["total"] / max_day * 100

    # Top Products
    top_products = (
        SaleItem.objects
        .values("product__product_name")
        .annotate(quantity=Sum("quantity"))
        .order_by("-quantity")[:5]
    )

    # Normalize top product bars
    max_qty = max([p["quantity"] for p in top_products], default=1)

    for item in top_products:
        item["percentage"] = (item["quantity"] / max_qty) * 100

    # Monthly Sales (NO JS chart)
    monthly_sales = (
        Sales.objects
        .annotate(month=TruncMonth("sale_date"))
        .values("month")
        .annotate(total=Sum("total_price"))
        .order_by("month")
    )

    max_total = max([m["total"] for m in monthly_sales], default=1)

    monthly_data = []

    for item in monthly_sales:
        monthly_data.append({
            "month": item["month"].strftime("%b %Y"),
            "total": item["total"],
            "percentage": (item["total"] / max_total) * 100
        })

    # Limit to last 6 months (clean UI)
    monthly_data = monthly_data[-6:]

    # Unpaid Customers
    unpaid_customers = Sales.objects.filter(
        customer_paid=False
    ).order_by("-sale_date")[:10]

    return render(request, "sales_dashboard.html", {
        "total_sales": total_sales,
        "unpaid_sales": unpaid_sales,
        "output_vat": output_vat,
        "total_invoices": total_invoices,
        "unpaid_count": unpaid_count,
        "average_sale": average_sale,
        "daily_sales": daily_sales,
        "top_products": top_products,
        "monthly_data": monthly_data,
        "unpaid_customers": unpaid_customers,
    })
    

