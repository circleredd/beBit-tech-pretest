from django.db import models
from rest_framework import serializers

# Create your models here.
class Order(models.Model):
    # Add your model here
    order_number = models.CharField(max_length=25, primary_key=True)
    total_price = models.IntegerField()
    created_time = models.DateTimeField(auto_now_add=True) # 資料建立時自動填入時間