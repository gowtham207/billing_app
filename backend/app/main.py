from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.deps import get_db
import uvicorn

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"service": settings.app_name, "docs": "/docs"}


@app.get("/api/v1/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


def _constraint(exc: IntegrityError) -> str | None:
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None)


@app.exception_handler(IntegrityError)
async def integrity_error(_request: Request, exc: IntegrityError):
    code = getattr(exc.orig, "sqlstate", None)
    name = _constraint(exc)
    if code == "23505":
        status, detail = 409, "Duplicate value"
    elif code in {"23514", "23503", "23502"}:
        status, detail = 422, "The request violates a database constraint"
    else:
        status, detail = 409, "Could not save the record"
    if name:
        detail = f"{detail} ({name})"
    return JSONResponse(status_code=status, content={"detail": detail})


@app.exception_handler(DataError)
async def data_error(_request: Request, _exc: DataError):
    return JSONResponse(status_code=422, content={"detail": "Invalid data for a database column"})


@app.exception_handler(ProgrammingError)
async def programming_error(_request: Request, exc: ProgrammingError):
    message = str(getattr(exc, "orig", exc))
    if "does not exist" in message or "organizations_for_user" in message:
        detail = "Database extras are missing. Apply database/app_extras.sql."
    else:
        detail = "Database request failed"
    return JSONResponse(status_code=500, content={"detail": detail})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
