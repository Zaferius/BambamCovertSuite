from sqlalchemy.orm import declarative_base
from app.models.job import Job  # noqa: E402
from app.models.user import User  # noqa: E402

Base = declarative_base()
