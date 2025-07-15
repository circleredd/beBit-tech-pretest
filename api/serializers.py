from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        # created_time 不讓 client 傳，所以只放前兩個欄位
        fields = ['order_number', 'total_price']

    def validate_total_price(self, value):
        if value < 0:
            raise serializers.ValidationError("total_price 不能為負數")
        return value