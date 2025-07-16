from django.shortcuts import render
# from django.http import HttpResponseBadRequest
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from functools import wraps
from django.db import transaction

from .serializers import OrderSerializer

def Auth(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.data.get("token") != ACCEPTED_TOKEN:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        # 驗證通過就執行後續 view
        return view_func(request, *args, **kwargs)
    return _wrapped_view



# Create your views here.
ACCEPTED_TOKEN = ('omni_pretest_token')


@api_view(['POST'])
@Auth
def import_order(request):
    # 從 request 取出 orders 清單，如果只有單筆也包成 list    
    orders_data = request.data.get('data', [])
    if isinstance(orders_data, dict):
        orders_data = [orders_data]
    
    # 若資料為空
    if not orders_data:
        return Response({"data": "請至少提供一筆訂單資料。"}, status=status.HTTP_400_BAD_REQUEST)

    # 用 Serializer 進行格式驗證
    serializer = OrderSerializer(data=orders_data, many=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 確保全數寫入或全數rollback
    with transaction.atomic():
        serializer.save()

    return Response(
        {
            "message": "Order created",
            "order": serializer.data
        },
        status=status.HTTP_201_CREATED
    )