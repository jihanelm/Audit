from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

from log_config import setup_logger

logger = setup_logger()

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

try:
    with engine.connect() as connection:
        logger.debug(f"DB_USER: {DB_USER}, DB_HOST: {DB_HOST}, DB_NAME: {DB_NAME}")
        logger.info("Connexion etablie avec la base de donnees avec succes")
except Exception as e:
    error_message = str(e.orig) if hasattr(e, 'orig') else str(e)
    logger.error(f"Erreur lors de la connexion à la base de données : {error_message}")
    raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

