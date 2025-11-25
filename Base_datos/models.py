from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class Docentes(Base):
    __tablename__ = 'Docentes'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    FECHA = Column(Integer)
    INSTITUCION_EDUCATIVA = Column(String(255))
    NIVEL = Column(String(100))
    IDIOMA = Column(String(255))
    
    
class Estudiantes_2016_2019(Base):
    __tablename__ = 'Estudiantes_2016_2019'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    FECHA = Column(Integer)
    SEDE_NODAL = Column(String(255))
    POBLACION = Column(String(150))
    NIVEL = Column(String(100))
    DIA = Column(String(255))
    JORNADA = Column(String(100))
    MATRICULADOS = Column(Integer)
    ETAPA = Column(Integer)

class Escuela_nueva(Base):
    __tablename__ = 'Escuela_nueva'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    FECHA = Column(Integer)
    SEDE = Column(String(255))
    INSTITUCION_EDUCATIVA = Column(String(255))
    GRUPO_1 = Column(Integer)
    GRUPO_2 = Column(Integer)
    GRUPO_3 = Column(Integer)
    MATRICULADOS = Column(Integer)