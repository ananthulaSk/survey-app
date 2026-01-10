from sqlalchemy import Column, Integer, String
from database import Base

class Voter(Base):
    __tablename__ = "voters"

    voter_id = Column(Integer, primary_key=True, index=True)
    ward_no = Column(Integer)
    serial_no = Column(Integer)
    house_no = Column(String)
    voter_name = Column(String)
    relation_name = Column(String)
    surname = Column(String)
    gender = Column(String)
    age = Column(Integer)
    family_id = Column(String)