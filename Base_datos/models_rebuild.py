from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Tipo_documentos(Base):
    __tablename__ = 'Tipo_documentos'
    ID = Column(BigInteger, primary_key=True, autoincrement=True)
    TIPO_DOCUMENTO = Column(String(100), nullable=False)

class Nivel_MCER(Base):
    __tablename__ = 'Nivel_MCER'
    ID = Column(BigInteger, primary_key=True, autoincrement=True)
    NIVEL_MCER = Column(String(100), nullable=False)
    TIPO_POBLACION = Column(String(100))
    ESTADO_ESTUDIANTE = Column(String(100))
    FECHA_ACTUAL = Column(String(100))  # Temporary as String to avoid date format issues

class Ciudades(Base):
    __tablename__ = 'Ciudades'
    ID = Column(BigInteger, primary_key=True, autoincrement=True)
    MUNICIPIO = Column(String(100), nullable=False)

class Instituciones_educativas(Base):
    __tablename__ = 'Instituciones_educativas'
    ID = Column(BigInteger, primary_key=True, autoincrement=True)
    INSTITUCION_EDUCATIVA = Column(String(200))
    COLEGIO_ABREVIADO = Column(String(100))
    GRADO = Column(String(50))

class Personas(Base):
    __tablename__ = 'Personas'
    ID = Column(BigInteger, primary_key=True, autoincrement=True)
    NOMBRES2 = Column(String(100))
    APELLIDOS = Column(String(100))
    TELEFONO1 = Column(String(50))
    TELEFONO2 = Column(String(50))
    NUMERO_DOCUMENTO = Column(BigInteger, unique=True)
    CORREO_ELECTRONICO = Column(String(200))
    DIRECCION = Column(String(200))
    SEXO = Column(String(20))
    FECHA_NACIMIENTO = Column(DateTime)
    CERTIFICADO = Column(BigInteger)
    TIPO_PERSONA = Column(String(50))
    TIPO_DOCUMENTO_ID = Column(BigInteger, ForeignKey('Tipo_documentos.ID'))
    NIVEL_MCER_ID = Column(BigInteger, ForeignKey('Nivel_MCER.ID'))
    CIUDAD_ID = Column(BigInteger, ForeignKey('Ciudades.ID'))

class Cursos(Base):
    __tablename__ = 'Cursos'
    ID = Column(BigInteger, primary_key=True, autoincrement=True)
    ENTIDAD = Column(String(200))
    NOMBRE_CURSO = Column(String(200))
    IDIOMA = Column(String(50))
    NIVEL_MCER_ID = Column(BigInteger, ForeignKey('Nivel_MCER.ID'))

class Sedes_instituciones(Base):
    __tablename__ = 'Sedes_instituciones'
    ID = Column(BigInteger, primary_key=True, autoincrement=True)
    GRUPO = Column(String(50))
    JORNADA = Column(String(50))
    FECHA_INICIAL = Column(DateTime)
    FECHA_FINAL = Column(DateTime)
    SEDE = Column(String(200))
    INSTITUCION_EDUCATIVA = Column(String(200))
    PERSONA_ID = Column(BigInteger, ForeignKey('Personas.ID'))