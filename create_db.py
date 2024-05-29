from database import engine, Base
from models import User, Item

try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(e)
