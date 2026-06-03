from django.urls import path
from stock import views


urlpatterns = [
    path("receipts/", views.stock_receipt_list, name="stock_receipt_list"),
    path("receipts/create/", views.create_stock_receipt, name="create_stock_receipt"),
    path("receipts/<int:receipt_id>/grn/", views.goods_received_note, name="goods_received_note"),
    path("receipts/<int:receipt_id>/edit/", views.edit_stock_receipt, name="edit_stock_receipt"),
    path("receipts/<int:receipt_id>/delete/", views.delete_stock_receipt, name="delete_stock_receipt"),
    path("report/", views.stock_report, name="stock_report"),
    path("report/export/", views.export_stock_report_excel, name="export_stock_report_excel"),
    path("stock-dashboard/", views.stock_dashboard, name="stock_dashboard"),
    
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.create_category, name="create_category"),
    path("categories/<int:category_id>/delete/", views.delete_category, name="delete_category"),

    path("products/", views.product_list, name="product_list"),
    path("products/create/", views.create_product, name="create_product"),
    path("products/<int:product_id>/edit/", views.edit_product, name="edit_product"),
    path("products/<int:product_id>/delete/", views.delete_product, name="delete_product"),
]