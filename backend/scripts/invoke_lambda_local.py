"""Call the Lambda handler on this machine, using backend/.env for the database."""

import os

os.environ.setdefault("AWS_LAMBDA_FUNCTION_NAME", "billing-api-local")

from app.lambda_handler import handler


def event(method: str, path: str) -> dict:
    return {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "rawQueryString": "",
        "headers": {"host": "localhost", "content-type": "application/json"},
        "requestContext": {
            "accountId": "local",
            "requestId": "local",
            "http": {"method": method, "path": path, "protocol": "HTTP/1.1", "sourceIp": "127.0.0.1"},
        },
        "isBase64Encoded": False,
    }


def main() -> None:
    for path in ("/", "/api/v1/health"):
        response = handler(event("GET", path), None)
        body = response.get("body") or ""
        print(path, response.get("statusCode"), body[:300])
        if response.get("statusCode") != 200:
            raise SystemExit(1)
    print("lambda-local-ok")


if __name__ == "__main__":
    main()
