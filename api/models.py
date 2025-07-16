from django.db import models

# Create your models here.


class Order(models.Model):
    # Add your model here
    order_number = models.CharField("訂單編號", max_length=25, primary_key=True)
    total_price = models.PositiveBigIntegerField("訂單總額")
    created_time = models.DateTimeField("建立時間", auto_now_add=True) # 資料建立時自動填入時間


