from alembic import context
from sqlalchemy import create_engine

from app.config import get_settings
from app.models import Base

# Tests pass their own URL via config attributes; otherwise use DATABASE_URL.
url = context.config.attributes.get("url") or get_settings().database_url
engine = create_engine(url)

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
