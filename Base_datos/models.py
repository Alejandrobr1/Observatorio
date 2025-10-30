from sqlalchemy import Column, Integer, String, Date, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

# Enum para nivel MCER
class NivelMCERType(enum.Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"
    SIN_DIAGNOSTICO = "SIN DIAGNOSTICO"

# Enum para tipo persona
class TipoPersonaType(enum.Enum):
    Docente = "Docente"
    Estudiante = "Estudiante"

class Tipo_documentos(Base):
    __tablename__ = 'Tipo_documentos'
    ID = Column(Integer, primary_key=True)
    TIPO_DOCUMENTO = Column(String(50), nullable=False)

class Nivel_MCER(Base):
    __tablename__ = 'Nivel_MCER'
    ID = Column(Integer, primary_key=True)
    NIVEL_MCER = Column(Enum(NivelMCERType), nullable=False)
    TIPO_POBLACION = Column(String(50))
    ESTADO_ESTUDIANTE = Column(String(50))
    FECHA_ACTUAL = Column(Date)
    personas = relationship("Personas", back_populates="nivel_mcer")
    cursos = relationship("Cursos", back_populates="nivel_mcer")

class Instituciones_educativas(Base):
    __tablename__ = 'Instituciones_educativas'
    ID = Column(Integer, primary_key=True)
    INSTITUCION_EDUCATIVA = Column(String(100))
    COLEGIO_ABREVIADO = Column(String(100))
    GRADO = Column(String(20))
    sedes_instituciones = relationship("Sedes_instituciones", back_populates="institucion_educativa")

class Ciudades(Base):
    __tablename__ = 'Ciudades'
    ID = Column(Integer, primary_key=True)
    MUNICIPIO = Column(String(100), nullable=False)
    personas = relationship("Personas", back_populates="ciudad")

class Personas(Base):
    __tablename__ = 'Personas'
    NOMBRES = Column(String(100))
    APELLIDOS = Column(String(100))
    TELEFONO1 = Column(String(20))
    TELEFONO2 = Column(String(20))
    NUMERO_DOCUMENTO = Column(Integer, primary_key=True)
    CORREO_ELECTRONICO = Column(String(100))
    DIRECCION = Column(String(200))
    SEXO = Column(String(20))
    FECHA_NACIMIENTO = Column(Date)
    CERTIFICADO = Column(String(100))
    TIPO_PERSONA = Column(Enum(TipoPersonaType), nullable=False)
    TIPO_DOCUMENTO_ID = Column(Integer, ForeignKey('Tipo_documentos.ID'))
    NIVEL_MCER_ID = Column(Integer, ForeignKey('Nivel_MCER.ID'))
    CIUDAD_ID = Column(Integer, ForeignKey('Ciudades.ID'))
    nivel_mcer = relationship("Nivel_MCER", back_populates="personas")
    ciudad = relationship("Ciudades", back_populates="personas")
    tipo_documento = relationship("Tipo_documentos")

class Cursos(Base):
    __tablename__ = 'Cursos'
    ID = Column(Integer, primary_key=True)
    ENTIDAD = Column(String(100))
    NOMBRE_CURSO = Column(String(100))
    IDIOMA = Column(String(50))
    NIVEL_MCER_ID = Column(Integer, ForeignKey('Nivel_MCER.ID'))
    SEDE = Column(String(100))
    nivel_mcer = relationship("Nivel_MCER", back_populates="cursos")
    sedes_instituciones = relationship("Sedes_instituciones", back_populates="curso")

class Sedes_instituciones(Base):
    __tablename__ = 'Sedes_instituciones'
    ID = Column(Integer, primary_key=True)
    CURSO_ID = Column(Integer, ForeignKey('Cursos.ID'))
    PERSONA_ID = Column(Integer, ForeignKey('Personas.NUMERO_DOCUMENTO'))  # AÑADIR ESTA LÍNEA
    GRUPO = Column(String(50))
    JORNADA = Column(String(50))
    FECHA_INICIAL = Column(Date)
    FECHA_FINAL = Column(Date)
    INSTITUCION_EDUCATIVA_ID = Column(Integer, ForeignKey('Instituciones_educativas.ID'))
    curso = relationship("Cursos", back_populates="sedes_instituciones")
    institucion_educativa = relationship("Instituciones_educativas", back_populates="sedes_instituciones")
    persona = relationship("Personas")  # AÑADIR ESTA LÍNEA

