from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import OperatingExpense
from decimal import Decimal
from django.db.models import Sum
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from users.decorators import accounts_required, admin_or_accounts_required
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
@admin_or_accounts_required
def expense_list(request):
    expenses = OperatingExpense.objects.all().order_by("-expense_date")
    total_amount = expenses.aggregate(total=Sum("amount"))["total"] or 0

    return render(request, "expense_list.html", {
        "expenses": expenses,
        "total_amount": total_amount
    })

@login_required
@admin_or_accounts_required
def add_expense(request):
    if request.method == "POST":
        
        if not request.POST.get("category") or not request.POST.get("amount") or not request.POST.get("expense_date"):
            messages.error(request, "Please fill in all required fields (Category, Amount, Expense Date).")
            return redirect("add_expense")
        
        OperatingExpense.objects.create(
            category=request.POST.get("category"),
            invoice_number=request.POST.get("invoice_number"),
            description=request.POST.get("description"),
            amount=request.POST.get("amount"),
            expense_date=request.POST.get("expense_date"),
            paid_to=request.POST.get("paid_to"),
            reference_number=request.POST.get("reference_number"),
            notes=request.POST.get("notes"),
            created_by=request.user.username if request.user.is_authenticated else "",
        )

        messages.success(request, "Expense added successfully.")
        return redirect("expense_list")

    return render(request, "add_expense.html", {
        "categories": OperatingExpense.EXPENSE_CATEGORIES
    })

@login_required
@admin_or_accounts_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(OperatingExpense, id=expense_id)

    if request.method == "POST":
        expense.category = request.POST.get("category")
        expense.invoice_number = request.POST.get("invoice_number")
        expense.description = request.POST.get("description")
        expense.amount = request.POST.get("amount")
        expense.expense_date = request.POST.get("expense_date")
        expense.paid_to = request.POST.get("paid_to")
        expense.reference_number = request.POST.get("reference_number")
        expense.notes = request.POST.get("notes")
        expense.save()

        messages.success(request, "Expense updated successfully.")
        return redirect("expense_list")

    return render(request, "edit_expense.html", {
        "expense": expense,
        "categories": OperatingExpense.EXPENSE_CATEGORIES
    })

@login_required
@admin_or_accounts_required    
def export_to_excel(filename, headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "Expenses Report"

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
def expense_report(request):
    expenses = OperatingExpense.objects.all().order_by("-expense_date")

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date:
        expenses = expenses.filter(expense_date__gte=start_date)

    if end_date:
        expenses = expenses.filter(expense_date__lte=end_date)

    total_expenses = expenses.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    if request.GET.get("export") == "excel":
        rows = []

        for expense in expenses:
            rows.append([
                expense.expense_date.strftime("%d-%m-%Y"),
                expense.get_category_display(),
                expense.invoice_number,
                expense.description,
                expense.paid_to,
                float(expense.amount),
                expense.reference_number,
                expense.created_by,
            ])

        rows.append([])
        rows.append([
            "Total Expenses", "", "", "", "", float(total_expenses), "", ""
        ])

        return export_to_excel(
            "expenses_report",
            [
                "Date",
                "Category",
                "Invoice No.",
                "Description",
                "Paid To",
                "Amount",
                "Reference",
                "Created By",
            ],
            rows
        )

    return render(request, "expense_report.html", {
        "expenses": expenses,
        "start_date": start_date,
        "end_date": end_date,
        "total_expenses": total_expenses,
    })