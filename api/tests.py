from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from api.views import ACCEPTED_TOKEN
from api.models import Order


# Create your tests here.
class OrderTestCase(APITestCase):
    # Add your testcase here
    def setUp(self):
        # 確保在 api/urls.py 中，path('import-order/', import_order, name='import-order')
        self.url = reverse('import-order')
        self.valid_token = ACCEPTED_TOKEN
        self.valid_payload = {
            'token': self.valid_token,
            'data': {
                'order_number': 'TEST123',
                'total_price': 999
            }
        }

    def test_no_token_unauthorized(self):
        """沒帶 token 應該回傳 401"""
        payload = {'data': {'order_number': 'A', 'total_price': 1}}
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp.data.get('detail'), 'Unauthorized')

    def test_invalid_data_bad_request(self):
        """帶錯誤欄位或型態，應該回傳 400 且包含欄位錯誤訊息"""
        payload = {
            'token': self.valid_token,
            'data': {
                'order_number': '',        # required, 不能為空
                'total_price': 'abc'       # 必須是整數
            }
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        # 驗證 serializer 回傳了欄位錯誤
        self.assertIn('order_number', resp.data)
        self.assertIn('total_price', resp.data)

    def test_success_creates_order(self):
        """正確 payload 應該建立一筆 Order 並回傳 201"""
        resp = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # DB 裡面要有一筆資料
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.order_number, 'TEST123')
        self.assertEqual(order.total_price, 999)

        # 回傳的 JSON 要帶回建立後的 order 資料
        self.assertIn('order', resp.data)
        self.assertEqual(resp.data['order']['order_number'], 'TEST123')
        self.assertEqual(resp.data['order']['total_price'], 999)


    def test_wrong_token_unauthorized(self):
        """帶錯 token 也要回 401"""
        payload = {
            'token': 'invalid_token',
            'data': {
                'order_number': 'A',
                'total_price': 1
            }
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp.data.get('detail'), 'Unauthorized')

    def test_missing_data_key_bad_request(self):
        """缺少 data 欄位，應回 400 且提示 order_number 必須存在"""
        payload = {
            'token': self.valid_token,
            # 'data' 整個欄位沒給
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        # 預期錯誤訊息會指出 order_number 與 total_price 必須提供
        self.assertIn('order_number', resp.data)
        self.assertIn('total_price', resp.data)

    def test_order_number_too_long(self):
        """order_number 超過 max_length=25，應回 400"""
        long_order_number = 'X' * 30
        payload = {
            'token': self.valid_token,
            'data': {
                'order_number': long_order_number,
                'total_price': 100
            }
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('order_number', resp.data)
        # 確認訊息含有 max_length 提示
        self.assertTrue(
            any('Ensure this field has no more than' in msg for msg in resp.data['order_number'])
        )

    def test_zero_total_price_creates_order(self):
        """total_price = 0 也可建立（預期），回傳 201 且資料庫有一筆"""
        payload = {
            'token': self.valid_token,
            'data': {
                'order_number': 'ZERO100',
                'total_price': 0
            }
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.get(order_number='ZERO100')
        self.assertEqual(order.total_price, 0)

    def test_negative_total_price_bad_request(self):
        """負數 total_price 不應儲存，回傳 400 且提示錯誤"""
        payload = {
            'token': self.valid_token,
            'data': {
                'order_number': 'NEG123',
                'total_price': -50
            }
        }
        resp = self.client.post(self.url, payload, format='json')

        # 1. HTTP 400
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. 錯誤欄位在 total_price
        self.assertIn('total_price', resp.data)

        # 3. 錯誤訊息符合我們在 Serializer 裡自訂的文字
        self.assertEqual(
            resp.data['total_price'][0],
            "total_price 不能為負數"
        )