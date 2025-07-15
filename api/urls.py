from django.contrib import admin
from django.urls import path
from api.views import import_order

urlpatterns = [
    path('import-order/', import_order, name='import-order')
]