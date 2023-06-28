import unittest
import json
import requests

class TestGUIDHandler(unittest.TestCase):
    base_url = 'http://localhost:8888/guid/'

    def test_post_guid(self):
        data = {'user': 'New User', 'expire': '1654070400'}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.base_url, data=json.dumps(data), headers=headers)
        self.assertEqual(response.status_code, 200)
        document = response.json()
        self.assertIn('guid', document)
        self.assertEqual(document['user'], 'New User')
        self.assertEqual(document['expire'], 1654070400)

    def test_get_guid(self):
        response = requests.get(self.base_url + '9094E4C980C74043A4B586B420E69DDF')
        self.assertEqual(response.status_code, 200)
        document = response.json()
        self.assertIn('guid', document)
        self.assertIn('user', document)
        self.assertIn('expire', document)

    def test_put_guid(self):
        data = {'user': 'Updated User', 'expire': '1654070400'}
        headers = {'Content-Type': 'application/json'}
        response = requests.put(self.base_url + '9094E4C980C74043A4B586B420E69DDF', data=json.dumps(data), headers=headers)
        self.assertEqual(response.status_code, 200)
        document = response.json()
        self.assertIn('guid', document)
        self.assertEqual(document['user'], 'Updated User')
        self.assertEqual(document['expire'], 1654070400)

    def test_delete_guid(self):
        response = requests.delete(self.base_url + '9094E4C980C74043A4B586B420E69DDF')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'successfully deleted')

if __name__ == '__main__':
    unittest.main()
