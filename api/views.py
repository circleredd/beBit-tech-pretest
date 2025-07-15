from django.shortcuts import render
# from django.http import HttpResponseBadRequest
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from functools import wraps

from .models import Order
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