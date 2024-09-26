import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_Name')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
engine = create_engine(f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}')

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# try:
#     with engine.connect() as connection:
#         print("Connected to the database via SQLAlchemy.")
#         result = connection.execute(text("SHOW TABLES;"))
#         tables = result.fetchall()
#         if tables:
#             print("Tables in the database:")
#             for table in tables:
#                 print(table[0])
#         else:
#             print("No tables found in the database.")

# except Exception as e:
#     print(f"Error connecting to the database: {e}")
