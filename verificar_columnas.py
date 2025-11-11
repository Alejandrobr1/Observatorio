from sqlalchemy import create_engine, inspect

engine = create_engine('mysql+mysqlconnector://root:123456@localhost:3308/observatorio_bilinguismo')
inspector = inspect(engine)

print("COLUMNAS EN Persona_Nivel_MCER:")
print("="*60)
cols = inspector.get_columns('Persona_Nivel_MCER')
for c in cols:
    print(f"  {c['name']}: {c['type']}")

print("\nCOLUMNAS EN Personas:")
print("="*60)
cols = inspector.get_columns('Personas')
for c in cols:
    print(f"  {c['name']}: {c['type']}")
