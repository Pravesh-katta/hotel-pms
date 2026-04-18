from django.urls import path

from . import views

urlpatterns = [
    path("", views.sales_report, name="reports_home"),
    path("sales/", views.sales_report, name="sales_report"),
    path("sales/export/", views.export_sales_csv, name="export_sales_csv"),
    path("occupancy/", views.occupancy_report, name="occupancy_report"),
    path("gst/", views.gst_report, name="gst_report"),
]
