from decimal import Decimal
from django.shortcuts import render
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from sales.models import Sales, SaleItem, Product
from stock.models import StockReceipt
from scheme.models import SchemeCustomer, SchemePayment, SchemeGoodsPickup
from openpyxl import Workbook
from openpyxl.styles import Font
from django.http import HttpResponse
from expenses.models import OperatingExpense
from django.contrib.auth.decorators import login_required
from users.decorators import admin_or_accounts_required

# Create your views here.
@login_required
@admin_or_accounts_required
def manager_dashboard(request):

    # SALES 
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

    # PROFIT 
    sale_items = SaleItem.objects.select_related("product")

    total_cost = Decimal("0.00")
    gross_profit = Decimal("0.00")

    for item in sale_items:
        cost = item.product.cost_price * item.quantity
        total_cost += cost
        gross_profit += item.total_price - cost

    profit_margin = (
        (gross_profit / total_sales) * 100
        if total_sales > 0 else Decimal("0.00")
    )

    # TOP PRODUCTS 
    top_products = (
        SaleItem.objects
        .values("product__product_name")
        .annotate(quantity=Sum("quantity"))
        .order_by("-quantity")[:5]
    )

    max_qty = max([p["quantity"] for p in top_products], default=1)
    for item in top_products:
        item["percentage"] = (item["quantity"] / max_qty) * 100

    # UNPAID CUSTOMERS 
    unpaid_customers = Sales.objects.filter(
        customer_paid=False
    ).order_by("-sale_date")[:10]

    # STOCK 
    products = Product.objects.all()

    total_stock_value = Decimal("0.00")
    low_stock_products = []

    for product in products:
        received = StockReceipt.objects.filter(product=product).aggregate(
            total=Sum("quantity_received")
        )["total"] or 0

        sold = SaleItem.objects.filter(product=product).aggregate(
            total=Sum("quantity")
        )["total"] or 0

        stock = received - sold
        total_stock_value += stock * product.cost_price

        if stock <= 5:
            low_stock_products.append({
                "product": product,
                "current_stock": stock
            })

    low_stock_count = len(low_stock_products)

    #  SUPPLIERS 
    total_supplier_payables = StockReceipt.objects.filter(
        supplier_paid=False
    ).aggregate(
        total=Sum("total_amount_due")
    )["total"] or Decimal("0.00")

    #  SCHEME -
    total_scheme_customers = SchemeCustomer.objects.count()

    total_deposits = SchemePayment.objects.aggregate(
        total=Sum("amount_paid")
    )["total"] or Decimal("0.00")

    goods_value = Decimal("0.00")
    for pickup in SchemeGoodsPickup.objects.select_related("linked_sale"):
        if pickup.linked_sale:
            goods_value += pickup.linked_sale.total_price

    scheme_balance = total_deposits - goods_value

    # ------------------ ALERTS ------------------
    alerts = []

    if unpaid_sales > 0:
        alerts.append({
            "type": "danger",
            "message": f"Unpaid sales: UGX {int(unpaid_sales):,}"
        })

    if low_stock_count > 0:
        alerts.append({
            "type": "warning",
            "message": f"{low_stock_count} low stock items"
        })

    if total_supplier_payables > 0:
        alerts.append({
            "type": "danger",
            "message": f"Supplier payables: UGX {int(total_supplier_payables):,}"
        })

    if scheme_balance < 0:
        alerts.append({
            "type": "danger",
            "message": "Scheme imbalance detected"
        })

    return render(request, "manager_dashboard.html", {
        "total_sales": total_sales,
        "unpaid_sales": unpaid_sales,
        "output_vat": output_vat,

        "gross_profit": gross_profit,
        "profit_margin": profit_margin,

        "top_products": top_products,
        "unpaid_customers": unpaid_customers,

        "total_stock_value": total_stock_value,
        "low_stock_count": low_stock_count,
        "low_stock_products": low_stock_products[:5],

        "total_supplier_payables": total_supplier_payables,

        "total_scheme_customers": total_scheme_customers,
        "total_deposits": total_deposits,
        "goods_value": goods_value,
        "scheme_balance": scheme_balance,

        "alerts": alerts,
    })

@login_required
@admin_or_accounts_required
def filter_by_date(request, queryset, date_field):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date:
        queryset = queryset.filter(**{f"{date_field}__date__gte": start_date})

    if end_date:
        queryset = queryset.filter(**{f"{date_field}__date__lte": end_date})

    return queryset, start_date, end_date

@login_required
@admin_or_accounts_required
def export_to_excel(filename, headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"

    ws.append(headers)

    for cell in ws[1]:
        cell.font = Font(bold=True)

    for row in rows:
        ws.append(row)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'

    wb.save(response)
    return response

@login_required
@admin_or_accounts_required
def reports_home(request):
    return render(request, "reports_home.html")

@login_required
@admin_or_accounts_required
def vat_report(request):
    sales, start_date, end_date = filter_by_date(
        request,
        Sales.objects.all(),
        "sale_date"
    )

    stock_receipts, _, _ = filter_by_date(
        request,
        StockReceipt.objects.all(),
        "date_received"
    )

    sale_items = SaleItem.objects.filter(sale__in=sales)

    output_vat = sale_items.aggregate(
        total=Sum("output_vat")
    )["total"] or Decimal("0.00")

    input_vat = stock_receipts.aggregate(
        total=Sum("input_vat")
    )["total"] or Decimal("0.00")

    vat_payable = output_vat - input_vat

    if request.GET.get("export") == "excel":
        rows = [
            ["Output VAT", float(output_vat)],
            ["Input VAT", float(input_vat)],
            ["VAT Payable", float(vat_payable)],
        ]

        return export_to_excel(
            "vat_report",
            ["Description", "Amount"],
            rows
        )

    return render(request, "vat_report.html", {
        "start_date": start_date,
        "end_date": end_date,
        "output_vat": output_vat,
        "input_vat": input_vat,
        "vat_payable": vat_payable,
    })

@login_required
@admin_or_accounts_required
def profit_loss_report(request):
    sales, start_date, end_date = filter_by_date(
        request,
        Sales.objects.all(),
        "sale_date"
    )

    sale_items = SaleItem.objects.filter(
        sale__in=sales
    ).select_related("product", "sale")

    total_revenue = sales.aggregate(
        total=Sum("total_price")
    )["total"] or Decimal("0.00")

    total_cost = Decimal("0.00")

    for item in sale_items:
        total_cost += item.product.cost_price * item.quantity

    gross_profit = total_revenue - total_cost

    expenses = OperatingExpense.objects.all()

    if start_date:
        expenses = expenses.filter(expense_date__gte=start_date)

    if end_date:
        expenses = expenses.filter(expense_date__lte=end_date)

    total_operating_expenses = expenses.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    net_profit = gross_profit - total_operating_expenses

    gross_profit_margin = Decimal("0.00")
    net_profit_margin = Decimal("0.00")

    if total_revenue > 0:
        gross_profit_margin = (gross_profit / total_revenue) * Decimal("100")
        net_profit_margin = (net_profit / total_revenue) * Decimal("100")

    if request.GET.get("export") == "excel":
        rows = [
            ["Total Revenue", float(total_revenue)],
            ["Cost of Goods Sold", float(total_cost)],
            ["Gross Profit", float(gross_profit)],
            ["Gross Profit Margin %", float(gross_profit_margin)],
            ["Operating Expenses", float(total_operating_expenses)],
            ["Net Profit", float(net_profit)],
            ["Net Profit Margin %", float(net_profit_margin)],
        ]

        return export_to_excel(
            "profit_loss_report",
            ["Description", "Amount"],
            rows
        )

    return render(request, "profit_loss_report.html", {
        "start_date": start_date,
        "end_date": end_date,
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "gross_profit": gross_profit,
        "gross_profit_margin": gross_profit_margin,
        "total_operating_expenses": total_operating_expenses,
        "net_profit": net_profit,
        "net_profit_margin": net_profit_margin,
        "expenses": expenses,
    })

@login_required
@admin_or_accounts_required
def payables_report(request):
    unpaid_receipts, start_date, end_date = filter_by_date(
        request,
        StockReceipt.objects.filter(
            supplier_paid=False
        ).select_related("product").order_by("-date_received"),
        "date_received"
    )

    total_payables = unpaid_receipts.aggregate(
        total=Sum("total_amount_due")
    )["total"] or Decimal("0.00")

    if request.GET.get("export") == "excel":
        rows = []

        for receipt in unpaid_receipts:
            rows.append([
                receipt.supplier_name,
                receipt.supplier_invoice_number,
                receipt.product.product_name,
                receipt.quantity_received,
                float(receipt.total_amount_due),
                receipt.date_received.strftime("%d-%m-%Y"),
            ])

        rows.append([])
        rows.append(["Total Payables", "", "", "", float(total_payables), ""])

        return export_to_excel(
            "payables_report",
            ["Supplier", "Invoice No.", "Product", "Quantity", "Amount Due", "Date"],
            rows
        )

    return render(request, "payables_report.html", {
        "start_date": start_date,
        "end_date": end_date,
        "unpaid_receipts": unpaid_receipts,
        "total_payables": total_payables,
    })

@login_required
@admin_or_accounts_required
def receivables_report(request):
    unpaid_sales, start_date, end_date = filter_by_date(
        request,
        Sales.objects.filter(
            customer_paid=False
        ).order_by("-sale_date"),
        "sale_date"
    )

    total_receivables = unpaid_sales.aggregate(
        total=Sum("total_price")
    )["total"] or Decimal("0.00")

    if request.GET.get("export") == "excel":
        rows = []

        for sale in unpaid_sales:
            rows.append([
                sale.customer_name,
                sale.customer_type,
                f"INV-{sale.id}",
                float(sale.total_price),
                sale.sale_date.strftime("%d-%m-%Y"),
            ])

        rows.append([])
        rows.append(["Total Receivables", "", "", float(total_receivables), ""])

        return export_to_excel(
            "receivables_report",
            ["Customer", "Customer Type", "Invoice", "Amount Due", "Date"],
            rows
        )

    return render(request, "receivables_report.html", {
        "start_date": start_date,
        "end_date": end_date,
        "unpaid_sales": unpaid_sales,
        "total_receivables": total_receivables,
    })

@login_required
@admin_or_accounts_required
def product_profitability_report(request):

    # Aggregate sales data per product
    sales_data = (
        SaleItem.objects
        .values(
            "product__id",
            "product__product_name",
            "product__cost_price"
        )
        .annotate(
            total_quantity=Sum("quantity"),
            total_revenue=Sum(
                ExpressionWrapper(
                    F("quantity") * F("selling_price"),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            )
        )
        .order_by("-total_revenue")  # highest revenue first
    )

    report = []

    total_revenue_all = Decimal("0.00")
    total_cost_all = Decimal("0.00")
    total_profit_all = Decimal("0.00")

    for item in sales_data:
        quantity = item["total_quantity"] or 0
        revenue = item["total_revenue"] or Decimal("0.00")
        cost_price = item["product__cost_price"] or Decimal("0.00")

        total_cost = quantity * cost_price
        profit = revenue - total_cost

        margin = (
            (profit / revenue) * Decimal("100")
            if revenue > 0 else Decimal("0.00")
        )

        total_revenue_all += revenue
        total_cost_all += total_cost
        total_profit_all += profit

        report.append({
            "product_name": item["product__product_name"],
            "quantity": quantity,
            "revenue": revenue,
            "cost": total_cost,
            "profit": profit,
            "margin": margin,
        })

    return render(request, "product_profitability.html", {
        "report": report,
        "total_revenue": total_revenue_all,
        "total_cost": total_cost_all,
        "total_profit": total_profit_all,
    })