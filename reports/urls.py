from django.urls import path
from . import views

urlpatterns = [
    path("reports/", views.reports_home, name="reports_home"),
    path("vat/", views.vat_report, name="vat_report"),
    path("profit-loss/", views.profit_loss_report, name="profit_loss_report"),
    path("payables/", views.payables_report, name="payables_report"),
    path("receivables/", views.receivables_report, name="receivables_report"),
    path("manager-dashboard/", views.manager_dashboard, name="manager_dashboard"),
    path("product_profitability/", views.product_profitability_report, name="product_profitability_report"),
]