from django.urls import path

from . import views

urlpatterns = [
    path("<int:folio_pk>/pay/", views.payment_page, name="payment_page"),
    path("<int:folio_pk>/pay/callback/", views.payment_callback, name="payment_callback"),
    path("<int:folio_pk>/cash/", views.cash_payment, name="cash_payment"),
    path("<int:folio_pk>/refund/", views.refund_view, name="refund"),
    path("<int:folio_pk>/invoice/", views.invoice_download, name="invoice_download"),
]
