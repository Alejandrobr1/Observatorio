from Base_datos.conexion import engine
import pandas as pd

print("\n" + "=" * 80)
print("🔍 VERIFICANDO CONEXIÓN A CLEVER CLOUD")
print("=" * 80 + "\n")

try:
    with engine.connect() as conn:
        # Contar personas
        df = pd.read_sql('SELECT COUNT(*) as total FROM Personas', conn)
        personas = df['total'].values[0]
        print(f"✅ Conexión a Clever Cloud exitosa")
        print(f"📊 Personas en BD: {personas}")
        
        # Ver tablas
        df_tables = pd.read_sql(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='bdldn022szfj4gyd9fqn'",
            conn
        )
        print(f"📋 Tablas: {len(df_tables)}")
        print(f"   {', '.join(df_tables['TABLE_NAME'].tolist())}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80 + "\n")
