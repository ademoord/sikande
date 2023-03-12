import unittest
from flask_app import app

class TestReportsRoute(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_reports_route(self):
        response = self.app.get('/reports')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()

