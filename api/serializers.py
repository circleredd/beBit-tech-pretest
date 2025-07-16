from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        # created_time 不讓 client 傳，所以只放前兩個欄位
        fields = ['order_number', 'total_price']