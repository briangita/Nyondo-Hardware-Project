from django.urls import path
from . import views

urlpatterns = [
    path("expenses/", views.expense_list, name="expense_list"),
    path("add/", views.add_expense, name="add_expense"),
    path("<int:expense_id>/edit/", views.edit_expense, name="edit_expense"),
    path('report/', views.expense_report, name='expense_report'),]