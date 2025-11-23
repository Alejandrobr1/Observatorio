from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Estudiantes_2016(Base):
    __tablename__ = 'Estudiantes_2016'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    FECHA = Column(Integer)
    SEDE_NODAL = Column(String(255))
    POBLACION = Column(String(150))
    NIVEL = Column(String(100))
    DIA = Column(String(255))
    JORNADA = Column(String(100))
    MATRICULADOS = Column(Integer)
    ETAPA = Column(Integer)
    
class Estudiantes_2017(Base):
    __tablename__ = 'Estudiantes_2017'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    FECHA = Column(Integer)
    SEDE_NODAL = Column(String(255))
    POBLACION = Column(String(150))
    NIVEL = Column(String(100))
    DIA = Column(String(255))
    JORNADA = Column(String(100))
    MATRICULADOS = Column(Integer)
    ETAPA = Column(Integer)
