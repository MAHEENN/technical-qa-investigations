
import json
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_URL = "http://127.0.0.1:8000/api/customers/4821"


def request_api(method, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None

    request = Request(
        BASE_URL,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


class CustomerAPITests(unittest.TestCase):

    def test_customer_email_update_persists(self):
        new_email = "regression@example.com"

        status, response = request_api(
            "PUT", {"email": new_email}
        )

        self.assertEqual(status, 200)
        self.assertTrue(response["success"])

        status, customer = request_api("GET")

        self.assertEqual(status, 200)
        self.assertEqual(customer["email"], new_email)

    def test_invalid_email_type_is_rejected(self):
        status, response = request_api(
            "PUT", {"email": 12345}
        )

        self.assertEqual(status, 400)
        self.assertEqual(response["error"], "Invalid email type")


if __name__ == "__main__":
    unittest.main()
