from django.shortcuts import render
# from django.http import HttpResponseBadRequest
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Order
from .serializers import OrderSerializer


# Create your views here.
ACCEPTED_TOKEN = ('omni_pretest_token')


@api_view(['POST'])
def import_order(request):
    # Add your code here
    if request.data.get("token") != ACCEPTED_TOKEN:
        return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    
    payload = request.data.get('data', {})

    # 用 Serializer 進行格式驗證
    serializer = OrderSerializer(data=payload)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 驗證通過後，save() 將在資料庫生成 Order 物件
    order = serializer.save()

    return Response(
        {
            "message": "Order created",
            "order": serializer.data
        },
        status=status.HTTP_201_CREATED
    )