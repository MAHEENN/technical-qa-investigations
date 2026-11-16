
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s"
)

customers = {
    4821: {
        "id": 4821,
        "email": "old@example.com"
    }
}

class CustomerAPI(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/api/customers/4821":
            return self.send_json(404, {"error": "Not found"})

        logging.info("Customer lookup requested")
        self.send_json(200, customers[4821])

    def do_PUT(self):
        if self.path != "/api/customers/4821":
            return self.send_json(404, {"error": "Not found"})

        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length)

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            logging.warning("Invalid JSON received")
            return self.send_json(400, {"error": "Invalid JSON"})

        logging.info("Customer update requested: %s", payload)

        if not isinstance(payload.get("email"), str):
            return self.send_json(400, {"error": "Invalid email type"})

        update_customer(4821, payload["email"])

        logging.info("Customer update processed")
        self.send_json(200, {
            "success": True,
            "message": "Customer updated successfully"
        })


def update_customer(customer_id, new_email):
    logging.info("Updating customer %s", customer_id)

    customers[customer_id]["email"] = new_email

    logging.info("Customer update operation completed")

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), CustomerAPI)
    print("Customer API running on http://127.0.0.1:8000")
    server.serve_forever()
