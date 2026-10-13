from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base

TEST_DATABASE_URL = (
    "postgresql+psycopg2://postgres:87654321@localhost:5432/task_management_test"
)

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)