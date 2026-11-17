from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

engine_kwargs = {"pool_pre_ping": True}
if settings.running_on_lambda:
    engine_kwargs["poolclass"] = NullPool
engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def set_organization(db: Session, organization_id) -> None:
    db.execute(
        text("SELECT set_config('app.current_organization_id', :value, true)"),
        {"value": "" if organization_id is None else str(organization_id)},
    )
