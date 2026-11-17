"""AWS Lambda entry point. Local development keeps using uvicorn."""

from mangum import Mangum

from app.main import app

handler = Mangum(app, lifespan="off")
