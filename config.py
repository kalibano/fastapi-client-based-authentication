from dotenv import load_dotenv
import os


load_dotenv()

DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
SECRETKEY = os.getenv("")
DEBUG = os.getenv("DEBUG")
