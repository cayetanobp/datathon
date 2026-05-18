import pandas as pd
from pathlib import Path

# =====================================================================
# 1. ENRUTAMIENTO DINÁMICO DESDE 'src/'
# =====================================================================
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

RUTA_MUNICIPIOS = RAIZ_PROYECTO / 'data' / 'municipios.csv'
RUTA_ENTRADA = RAIZ_PROYECTO / 'data' / 'restaurantes_con_grupo_cp.csv'
# Definimos el nuevo archivo CSV de salida para los códigos postales
RUTA_SALIDA_CSV = RAIZ_PROYECTO / 'data' / 'resumen_restaurantes_cp.csv'

print("📊 [src] Generando resumen estadístico de restaurantes por Código Postal...")

if not RUTA_ENTRADA.exists() or not RUTA_MUNICIPIOS.exists():
    print(f"❌ ERROR: Asegúrate de que los archivos existan en la carpeta 'data/'")
    exit()

# =====================================================================
# 2. CARGA DE DATOS Y LIMPIEZA DE CÓDIGOS POSTALES
# =====================================================================
df_mun = pd.read_csv(RUTA_MUNICIPIOS)
df_rest = pd.read_csv(RUTA_ENTRADA, sep=';')

# Convertimos los códigos postales a enteros limpios (ej: 29620.0 -> 29620)
# Los vacíos se marcan temporalmente como 0
df_rest['Codigo_Postal_Clean'] = pd.to_numeric(df_rest['Codigo_Postal'], errors='coerce').fillna(0).astype(int)

# =====================================================================
# 3. CREACIÓN DEL DICCIONARIO PARA CONTROLAR EL MUNICIPIO
# =====================================================================
def desglosar_codigos_postales(cp_str):
    cp_str = str(cp_str).strip().replace('\n', '')
    if '-' in cp_str:
        inicio, fin = cp_str.split('-')
        return list(range(int(inicio.strip()), int(fin.strip()) + 1))
    else:
        return [int(cp_str)]

mapa_cp_a_municipio = {}
for _, fila in df_mun.iterrows():
    mun_oficial = fila['Municipio / Zona'].strip()
    for cp in desglosar_codigos_postales(fila['Rango / Códigos Postales']):
        mapa_cp_a_municipio[cp] = mun_oficial

# =====================================================================
# 4. AGRUPACIÓN, CONTEO Y MAPEO DEL MUNICIPIO
# =====================================================================
# Contamos cuántos restaurantes hay en cada código postal
resumen_cp = df_rest['Codigo_Postal_Clean'].value_counts().reset_index()
resumen_cp.columns = ['Codigo_Postal', 'Cantidad_Restaurantes']

# Vinculamos cada CP a su Municipio Oficial
resumen_cp['Municipio'] = resumen_cp['Codigo_Postal'].map(mapa_cp_a_municipio)

# Gestionamos los CP que no tengan correspondencia o sean 0
resumen_cp['Municipio'] = resumen_cp['Municipio'].fillna('Sin clasificar / Vacío')
resumen_cp['Codigo_Postal'] = resumen_cp['Codigo_Postal'].replace(0, 'Vacío/Desconocido')

# =====================================================================
# 5. GUARDAR EN UN NUEVO ARCHIVO CSV Y MOSTRAR TOP 15
# =====================================================================
resumen_cp.to_csv(RUTA_SALIDA_CSV, sep=';', index=False)

print("\n" + "="*70)
print(f"   TOP 15 CÓDIGOS POSTALES CON MÁS RESTAURANTES")
print("="*70)
print(f"{'Cód. Postal':<18} | {'Municipio':<25} | {'Nº Restaurantes'}")
print("-"*70)

# Mostramos los 15 primeros por consola para verificar
for _, fila in resumen_cp.head(15).iterrows():
    print(f"📌 {str(fila['Codigo_Postal']):<14} | {fila['Municipio']:<25} | {fila['Cantidad_Restaurantes']} locales")

print("="*70)
print(f"💾 El nuevo CSV detallado se ha guardado en: '{RUTA_SALIDA_CSV}'")