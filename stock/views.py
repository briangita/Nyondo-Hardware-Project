from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from sales.models import  SaleItem
from .models import StockReceipt, Category , Product
from django.http import HttpResponse
from openpyxl import Workbook
from django.db import IntegrityError
from decimal import Decimal, InvalidOperation
from django.contrib import messages # For user feedback messages
from users.decorators import admin_required, admin_or_store_manager_required, admin_or_accounts_or_store_manager_required
from django.contrib.auth.decorators import login_required


# Create your views here.

@login_required
@admin_or_store_manager_required
def stock_receipt_list(request):
    receipts = StockReceipt.objects.all().order_by("-date_received")
    return render(request, "stock_receipt_list.html", {
        "receipts": receipts
    })

@login_required
@admin_or_store_manager_required
def create_stock_receipt(request):
    products = Product.objects.all()

    if request.method == "POST":
        errors = {}
        data = request.POST

        try:
            product_id = data.get("product")
            product = Product.objects.filter(id=product_id).first()

            supplier_name = data.get("supplier_name", "").strip()
            supplier_invoice_number = data.get("supplier_invoice_number", "").strip()

            quantity_received = int(data.get("quantity_received") or 0)
            unit_cost = Decimal(data.get("unit_cost") or 0)
            retail_price = Decimal(data.get("retail_price") or 0)
            wholesale_price = Decimal(data.get("wholesale_price") or 0)

            vat_applicable = data.get("vat_applicable") == "on"
            supplier_paid = data.get("supplier_paid") == "on"

            if not product:
                errors["product"] = "Please select a valid product."

            if not supplier_name:
                errors["supplier_name"] = "Supplier name is required."

            if not supplier_invoice_number:
                errors["supplier_invoice_number"] = "Invoice number is required."

            if quantity_received <= 0:
                errors["quantity_received"] = "Must be greater than zero."

            if unit_cost <= 0:
                errors["unit_cost"] = "Must be greater than zero."

            if retail_price <= 0:
                errors["retail_price"] = "Must be greater than zero."
            elif retail_price <= unit_cost:
                errors["retail_price"] = "Must be greater than unit cost."

            if wholesale_price <= 0:
                errors["wholesale_price"] = "Must be greater than zero."
            elif wholesale_price <= unit_cost:
                errors["wholesale_price"] = "Must be greater than unit cost."
            elif wholesale_price >= retail_price:
                errors["wholesale_price"] = "Must be less than retail price."

            if errors:
                return render(request, "create_stock_receipt.html", {
                    "products": products,
                    "errors": errors,
                    "data": data
                })

            receipt = StockReceipt.objects.create(
                product=product,
                supplier_name=supplier_name,
                supplier_invoice_number=supplier_invoice_number,
                quantity_received=quantity_received,
                unit_cost=unit_cost,
                retail_price=retail_price,
                wholesale_price=wholesale_price,
                vat_applicable=vat_applicable,
                supplier_paid=supplier_paid
            )

            return redirect("goods_received_note", receipt_id=receipt.id)

        except (ValueError, InvalidOperation):
            errors["general"] = "Please enter valid entries in the form."

            return render(request, "create_stock_receipt.html", {
                "products": products,
                "errors": errors,
                "data": data
            })

    return render(request, "create_stock_receipt.html", {
        "products": products
    })

@login_required
@admin_or_store_manager_required
def goods_received_note(request, receipt_id):
    receipt = get_object_or_404(StockReceipt, id=receipt_id)

    return render(request, "goods_received_note.html", {
        "receipt": receipt
    })

@login_required
@admin_or_store_manager_required
def edit_stock_receipt(request, receipt_id):
    receipt = get_object_or_404(StockReceipt, id=receipt_id)
    products = Product.objects.all()

    if request.method == "POST":
        errors = {}
        data = request.POST

        try:
            product_id = data.get("product")
            product = Product.objects.filter(id=product_id).first()

            supplier_name = data.get("supplier_name", "").strip()
            quantity_received = int(data.get("quantity_received") or 0)
            unit_cost = Decimal(data.get("unit_cost") or 0)
            retail_price = Decimal(data.get("retail_price") or 0)
            wholesale_price = Decimal(data.get("wholesale_price") or 0)

            supplier_paid = data.get("supplier_paid") == "on"

            if not product:
                errors["product"] = "Please select a valid product."

            if not supplier_name:
                errors["supplier_name"] = "Supplier name is required."

            if quantity_received <= 0:
                errors["quantity_received"] = "Must be greater than zero."

            if unit_cost <= 0:
                errors["unit_cost"] = "Must be greater than zero."

            if retail_price <= 0:
                errors["retail_price"] = "Must be greater than zero."
            elif retail_price <= unit_cost:
                errors["retail_price"] = "Must be greater than unit cost."

            if wholesale_price <= 0:
                errors["wholesale_price"] = "Must be greater than zero."
            elif wholesale_price <= unit_cost:
                errors["wholesale_price"] = "Must be greater than unit cost."
            elif wholesale_price >= retail_price:
                errors["wholesale_price"] = "Must be less than retail price."

            if errors:
                return render(request, "edit_stock_receipt.html", {
                    "receipt": receipt,
                    "products": products,
                    "errors": errors,
                    "data": data
                })

            receipt.product = product
            receipt.supplier_name = supplier_name
            receipt.quantity_received = quantity_received
            receipt.unit_cost = unit_cost
            receipt.retail_price = retail_price
            receipt.wholesale_price = wholesale_price
            receipt.supplier_paid = supplier_paid

            receipt.save()

            messages.success(request, "Receipt updated successfully.")
            return redirect("stock_receipt_list")

        except (ValueError, InvalidOperation):
            return render(request, "edit_stock_receipt.html", {
                "receipt": receipt,
                "products": products,
                "errors": {"general": "Please enter valid numbers."},
                "data": data
            })

    return render(request, "edit_stock_receipt.html", {
        "receipt": receipt,
        "products": products
    })

@login_required
@admin_required
def delete_stock_receipt(request, receipt_id):
    receipt = get_object_or_404(StockReceipt, id=receipt_id)

    if request.method == "POST":
        receipt.delete()
        return redirect("stock_receipt_list")

    return render(request, "delete_stock_receipt.html", {
        "receipt": receipt
    })

@login_required
@admin_or_accounts_or_store_manager_required
def stock_report(request):
    products = Product.objects.all()

    report = []
    total_stock_value = Decimal("0.00")

    for product in products:

        total_received = StockReceipt.objects.filter(
            product=product
        ).aggregate(
            total=Sum("quantity_received")
        )["total"] or 0

        total_sold = SaleItem.objects.filter(
            product=product
        ).aggregate(
            total=Sum("quantity")
        )["total"] or 0

        current_stock = total_received - total_sold

        # Stock status
        if current_stock <= 5:
            status = "Low Stock"
        elif current_stock <= 20:
            status = "Medium Stock"
        else:
            status = "High Stock"

        stock_value = current_stock * product.cost_price
        total_stock_value += stock_value

        report.append({
            "product": product,
            "total_received": total_received,
            "total_sold": total_sold,
            "current_stock": current_stock,
            "status": status,
            "stock_value": stock_value
        })

    # ✅ Fast Selling Items (NEW)
    fast_selling_items = (
        SaleItem.objects
        .values("product__product_name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )

    return render(request, "stock_report.html", {
        "report": report,
        "total_stock_value": total_stock_value,
        "fast_selling_items": fast_selling_items,  # NEW
    })

@login_required
@admin_or_accounts_or_store_manager_required
def export_stock_report_excel(request):
    products = Product.objects.all()

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Stock Report"

    worksheet.append([
        "Product",
        "Category",
        "Total Received",
        "Total Sold",
        "Current Stock",
        "Status",
        "Stock Value"
    ])

    for product in products:
        total_received = StockReceipt.objects.filter(
            product=product
        ).aggregate(total=Sum("quantity_received"))["total"] or 0

        total_sold = SaleItem.objects.filter(
            product=product
        ).aggregate(total=Sum("quantity"))["total"] or 0

        current_stock = total_received - total_sold

        if current_stock <= 5:
            status = "Low Stock"
        elif current_stock <= 20:
            status = "Medium Stock"
        else:
            status = "High Stock"

        worksheet.append([
            product.product_name,
            product.category_name.category_name,
            total_received,
            total_sold,
            current_stock,
            status,
            current_stock * product.cost_price,
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = 'attachment; filename="stock_report.xlsx"'

    workbook.save(response)

    return response

@login_required
@admin_or_store_manager_required
def stock_dashboard(request):
    products = Product.objects.all()

    total_stock_value = Decimal("0.00")
    low_stock_products = []
    stock_levels = []

    for product in products:
        total_received = StockReceipt.objects.filter(
            product=product
        ).aggregate(
            total=Sum("quantity_received")
        )["total"] or 0

        total_sold = SaleItem.objects.filter(
            product=product
        ).aggregate(
            total=Sum("quantity")
        )["total"] or 0

        current_stock = total_received - total_sold
        stock_value = product.cost_price * current_stock

        total_stock_value += stock_value

        stock_levels.append({
            "product": product.product_name,
            "stock": current_stock,
        })

        if current_stock <= 5:
            low_stock_products.append({
                "product": product,
                "current_stock": current_stock,
            })

    paid_suppliers = StockReceipt.objects.filter(
        supplier_paid=True
    ).order_by("-date_received")[:10]

    unpaid_suppliers = StockReceipt.objects.filter(
        supplier_paid=False
    ).order_by("-date_received")[:10]

    return render(request, "stock_dashboard.html", {
        "total_stock_value": total_stock_value,
        "low_stock_count": len(low_stock_products),
        "low_stock_products": low_stock_products[:5],
        "stock_levels": stock_levels[:10],
        "paid_suppliers": paid_suppliers,
        "unpaid_suppliers": unpaid_suppliers,
    })

@login_required
@admin_or_store_manager_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, "category_list.html", {"categories": categories})

@login_required
@admin_or_store_manager_required
def create_category(request):
    if request.method == "POST":
        category_name = request.POST.get("category_name")
        description = request.POST.get("description")

        try:
            Category.objects.create(
                category_name=category_name,
                description=description
            )
            return redirect("category_list")

        except IntegrityError:
            return render(request, "create_category.html", {
                "error": "This category already exists."
            })

    return render(request, "create_category.html")

@login_required
@admin_or_store_manager_required
def product_list(request):
    products = Product.objects.all()
    return render(request, "product_list.html", {"products": products})

@login_required
@admin_or_store_manager_required
def create_product(request):
    categories = Category.objects.all()

    if request.method == "POST":
        category = get_object_or_404(Category, id=request.POST.get("category"))
        product_name = request.POST.get("product_name")
        retail_price = request.POST.get("retail_price")
        wholesale_price = request.POST.get("wholesale_price")
        description = request.POST.get("description")

        if not product_name:
            messages.error(request, "Product name is required.")
            return render(request, "create_product.html", {"categories": categories})

        if not category:
            messages.error(request, "Please select a valid category.")
            return render(request, "create_product.html", {"categories": categories})

        Product.objects.create(
            category_name=category,
            product_name=product_name,
            retail_price=retail_price,
            wholesale_price=wholesale_price,
            description=description
        )

        return redirect("product_list")

    return render(request, "create_product.html", {
        "categories": categories
    })

@login_required
@admin_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.delete()
        return redirect("product_list")

    return render(request, "delete_product.html", {
        "product": product
    })

@login_required
@admin_or_store_manager_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()

    if request.method == "POST":
        category = get_object_or_404(Category, id=request.POST.get("category"))
        product_name = request.POST.get("product_name")
        retail_price = request.POST.get("retail_price")
        wholesale_price = request.POST.get("wholesale_price")
        description = request.POST.get("description")
        
        if not product_name:
            messages.error(request, "Product name is required.")
            return render(request, "edit_product.html", {
                "product": product,
                "categories": categories
            })
        if not category:
            messages.error(request, "Please select a valid category.")
            return render(request, "edit_product.html", {
                "product": product,
                "categories": categories
            })

        product.category_name = category
        product.product_name = product_name
        product.retail_price = retail_price
        product.wholesale_price = wholesale_price
        product.description = description
        product.save()

        return redirect("product_list")

    return render(request, "edit_product.html", {
        "product": product,
        "categories": categories
    })

@login_required
@admin_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        category.delete()
        return redirect("category_list")

    return render(request, "delete_category.html", {
        "category": category
    })