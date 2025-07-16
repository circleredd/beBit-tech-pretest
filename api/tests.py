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
        error = resp.data[0]
        self.assertIn('order_number', error)
        self.assertIn('total_price', error)
    
    def test_bulk_one_invalid_bad_request(self):
        """多筆匯入時，其中一筆格式錯誤，應回 400 且不會建立任何訂單"""
        payload = {
            'token': self.valid_token,
            'data': [
                {'order_number': 'OK001', 'total_price': 100},
                {'order_number': '',      'total_price': 200},  # 錯誤：order_number 不能為空
                {'order_number': 'OK003', 'total_price': 300},
            ]
        }
        resp = self.client.post(self.url, payload, format='json')

        # 1. HTTP 狀態碼應為 400
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. Atomically rollback：DB 中不應該有任何資料
        self.assertEqual(Order.objects.count(), 0)

        # 3. resp.data 應該是一個 list，長度等於輸入筆數
        self.assertIsInstance(resp.data, list)
        self.assertEqual(len(resp.data), 3)

        # 4. 第 1 筆與第 3 筆無錯誤（空 dict），第 2 筆要有 order_number 的錯誤
        self.assertEqual(resp.data[0], {})
        self.assertEqual(resp.data[2], {})

        err_item = resp.data[1]
        self.assertIn('order_number', err_item)
        self.assertTrue(
            any(
                'may not be blank' in str(msg) or 'blank' in str(msg)
                for msg in err_item['order_number']
            )
        )

    def test_success_creates_order(self):
        """正確 payload 應該建立一筆 Order 並回傳 201"""
        resp = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # DB 裡面要有一筆資料
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.order_number, 'TEST123')
        self.assertEqual(order.total_price, 999)

        # 回傳的 JSON 要帶回建立後的 order 資料（list）
        self.assertIn('order', resp.data)
        self.assertIsInstance(resp.data['order'], list)
        self.assertEqual(len(resp.data['order']), 1)

        returned = resp.data['order'][0]
        self.assertEqual(returned['order_number'], 'TEST123')
        self.assertEqual(returned['total_price'], 999)


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
        self.assertIn('data', resp.data)
        self.assertEqual(resp.data['data'], "請至少提供一筆訂單資料。")

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

        # 取出第一筆錯誤 dict
        first_error = resp.data[0]
        self.assertIn('order_number', first_error)

        # 確認訊息含有 max_length 提示
        errors = first_error['order_number']
        self.assertTrue(
            any(
                'Ensure this field has no more than 25 characters.' in str(msg)
                for msg in errors
            )
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

        #  HTTP 400
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # 取出第一筆錯誤 dict
        first_error = resp.data[0]

        # 取出錯誤 list，並檢查訊息內容
        errors = first_error['total_price']
        self.assertIsInstance(errors, list)
        
        # 至少有一條訊息包含 “greater than or equal to 0”
        self.assertTrue(
            any(
                'greater than or equal to 0' in str(msg)
                for msg in errors
            )
        )

    def test_bulk_create_orders(self):
        """多筆匯入 -> 201, 建立多筆"""
        payload = {
            'token': self.valid_token,
            'data': [
                {'order_number': 'A1', 'total_price': 10},
                {'order_number': 'B2', 'total_price': 20},
            ]
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2)
        numbers = [o['order_number'] for o in resp.data['order']]
        self.assertListEqual(sorted(numbers), ['A1', 'B2'])