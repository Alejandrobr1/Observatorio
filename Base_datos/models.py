from sqlalchemy import Column, BigInteger, String, ForeignKey, Integer, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import Date

Base = declarative_base()

# ==========================================
# TABLA DE ASOCIACIÓN PARA RELACIÓN MUCHOS-A-MUCHOS
# ==========================================
# Esta tabla intermedia conecta Personas con Nivel_MCER
Persona_Nivel_MCER = Table(
    'Persona_Nivel_MCER',
    Base.metadata,
    Column('ID', BigInteger, primary_key=True, autoincrement=True),
    Column('PERSONA_ID', BigInteger, ForeignKey('Personas.ID'), nullable=False),
    Column('NIVEL_MCER_ID', BigInteger, ForeignKey('Nivel_MCER.ID'), nullable=False),
    Column('ANIO_REGISTRO', Integer),  # Año en que la persona obtuvo este nivel
)

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
    ANIO = Column(Integer)
    IDIOMA = Column(String(100))
    CERTIFICADO = Column(String(50))
    GRADO = Column(String(50))  # NUEVO: Movido desde Instituciones

class Ciudades(Base):
    __tablename__ = 'Ciudades'
    ID = Column(BigInteger, primary_key=True, autoincrement=True)
    MUNICIPIO = Column(String(100), nullable=False)

class Instituciones(Base):
    __tablename__ = 'Instituciones'
    ID = Column(BigInteger, primary_key=True, autoincrement=True)
    NOMBRE_INSTITUCION = Column(String(200))
    COLEGIO_ABREVIADO = Column(String(100))
    # GRADO eliminado de aquí

class Personas(Base):
    __tablename__ = 'Personas'
    ID = Column(BigInteger, primary_key=True, autoincrement=True)
    NOMBRES = Column(String(100))
    APELLIDOS = Column(String(100))
    TELEFONO1 = Column(String(50))
    TELEFONO2 = Column(String(50))
    NUMERO_DOCUMENTO = Column(String(50), unique=True)
    CORREO_ELECTRONICO = Column(String(200))
    DIRECCION = Column(String(200))
    SEXO = Column(String(20))
    FECHA_NACIMIENTO = Column(Date)
    TIPO_PERSONA = Column(String(50))
    TIPO_DOCUMENTO_ID = Column(BigInteger, ForeignKey('Tipo_documentos.ID'))
    # NIVEL_MCER_ID eliminado (ahora es relación muchos-a-muchos)
    CIUDAD_ID = Column(BigInteger, ForeignKey('Ciudades.ID'))
    INSTITUCION_ID = Column(BigInteger, ForeignKey('Instituciones.ID'))

class Cursos(Base):
    __tablename__ = 'Cursos'
    ID = Column(BigInteger, primary_key=True, autoincrement=True)
    NOMBRE_CURSO = Column(String(200))
    ENTIDAD = Column(String(200))
    IDIOMA = Column(String(50))
    INSTITUCION_ID = Column(BigInteger, ForeignKey('Instituciones.ID'))

class Sedes(Base):
    __tablename__ = 'Sedes'
    ID = Column(BigInteger, primary_key=True, autoincrement=True)
    GRUPO = Column(String(255))
    JORNADA = Column(String(255))
    SEDE_NODAL = Column(String(200))
    PERSONA_ID = Column(BigInteger, ForeignKey('Personas.ID'))
