from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

db_username = "smartpay_user"
db_password = "Srikar123"
db_host = "localhost"
db_port = "3306"
db_name = "smartpay_db"

DATABASE_URL = (
    f"mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
)


engine = create_engine(DATABASE_URL,pool_pre_ping=True)

SessionLocal = sessionmaker( autocommit=False,autoflush=False,bind=engine)
Base = declarative_base()
