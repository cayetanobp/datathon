import pandas as pd
from pathlib import Path

# =====================================================================
# 1. ENRUTAMIENTO DESDE LA CARPETA 'src/'
# =====================================================================
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_ENTRADA = RAIZ_PROYECTO / 'data' / 'restaurantes_con_grupo_cp.csv'
# Definimos la ruta de salida para el nuevo CSV
RUTA_SALIDA_CSV = RAIZ_PROYECTO / 'data' / 'resumen_restaurantes_grupos.csv'

print("📊 [src] Generando resumen estadístico de restaurantes por Grupo...")

if not RUTA_ENTRADA.exists():
    print(f"❌ ERROR: No se encuentra el archivo en: {RUTA_ENTRADA}")
    print("👉 Asegúrate de haber ejecutado primero el script 'clasificar_por_cp.py'")
    exit()

# 2. CARGA DE DATOS SEGURA
df = pd.read_csv(RUTA_ENTRADA, sep=';')
df['Grupo'] = df['Grupo'].astype(str).fillna('').str.strip()

# 3. AGRUPACIÓN Y CONTEO
resumen = df['Grupo'].value_counts().reset_index()
resumen.columns = ['Grupo', 'Cantidad_Restaurantes']

resumen['Grupo'] = resumen['Grupo'].replace({'': 'Sin Grupo asignado (CP fuera de rango o vacío)', 
                                             'nan': 'Sin Grupo asignado (CP fuera de rango o vacío)'})

# =====================================================================
# 4. EXPORTAR LOS RESULTADOS A UN ARCHIVO CSV
# =====================================================================
resumen.to_csv(RUTA_SALIDA_CSV, sep=';', index=False)

# 5. MOSTRAR RESULTADOS POR PANTALLA
print("\n" + "="*60)
print(f"   RESUMEN TOTAL: {len(df)} RESTAURANTES CLASIFICADOS")
print("="*60)

for _, fila in resumen.iterrows():
    print(f"📍 {fila['Grupo']:<45} : {fila['Cantidad_Restaurantes']} locales")

print("="*60)
print(f"💾 Archivo estadístico guardado en: '{RUTA_SALIDA_CSV}'")