import pandas as pd
import os
from pathlib import Path

# =====================================================================
# 1. CONFIGURACIÓN DE RUTAS DINÁMICAS (Para ejecutar desde cualquier carpeta)
# =====================================================================
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

# Rutas de entrada y salida
RUTA_MUNICIPIOS = RAIZ_PROYECTO / 'data' / 'municipios.csv'
RUTA_RESTAURANTES = RAIZ_PROYECTO / 'data' / 'restaurantes_filtrados_malaga.csv'
RUTA_NUEVO_ARCHIVO = RAIZ_PROYECTO / 'data' / 'restaurantes_con_grupo_cp.csv'

print("🔄 Iniciando proceso de clasificación estricta por Código Postal...")

# Comprobación de seguridad
if not RUTA_MUNICIPIOS.exists() or not RUTA_RESTAURANTES.exists():
    print("❌ ERROR: Asegúrate de que los archivos existan dentro de la carpeta 'data/'")
    exit()

# =====================================================================
# 2. CARGA DE ARCHIVOS
# =====================================================================
df_mun = pd.read_csv(RUTA_MUNICIPIOS)
df_rest = pd.read_csv(RUTA_RESTAURANTES, sep=';')

# =====================================================================
# 3. PROCESAMIENTO Y DESGLOSE DE LOS RANGOS EN MUNICIPIOS.CSV
# =====================================================================
def desglosar_codigos_postales(cp_str):
    """Convierte cadenas como '29630 - 29639' o '29130' en una lista de enteros."""
    cp_str = str(cp_str).strip().replace('\n', '')
    if '-' in cp_str:
        inicio, fin = cp_str.split('-')
        return list(range(int(inicio.strip()), int(fin.strip()) + 1))
    else:
        return [int(cp_str)]

# Creamos el mapa maestro: { 29630: "benalmadena", 29631: "benalmadena", ... }
mapa_cp_a_grupo = {}
for _, fila in df_mun.iterrows():
    grupo_oficial = str(fila['Grupo']).strip()
    lista_cps = desglosar_codigos_postales(fila['Rango / Códigos Postales'])
    for cp in lista_cps:
        mapa_cp_a_grupo[cp] = grupo_oficial

# =====================================================================
# 4. APLICACIÓN DE LA REGLA AL ARCHIVO DE RESTAURANTES
# =====================================================================
def buscar_grupo_por_cp(cp_valor):
    """Busca el grupo en base al CP. Si no existe o da error, devuelve vacío."""
    if pd.isna(cp_valor):
        return ""
    try:
        # Convertimos a entero (maneja formatos float como 29640.0 limpiamente)
        cp_int = int(float(cp_valor))
        # Buscamos en el diccionario. Si no existe, devuelve una cadena vacía ""
        return mapa_cp_a_grupo.get(cp_int, "")
    except (ValueError, TypeError):
        return ""

# Creamos/Sobreescribimos la columna Grupo basándonos únicamente en el CP
df_rest['Grupo'] = df_rest['Codigo_Postal'].apply(buscar_grupo_por_cp)

# =====================================================================
# 5. REORGANIZACIÓN ESTÉTICA DE COLUMNAS Y GUARDADO
# =====================================================================
# Si la columna ya existía, la quitamos de su sitio original para reubicarla de forma elegante
columnas = list(df_rest.columns)
if 'Grupo' in columnas:
    columnas.remove('Grupo')

# Colocamos la columna 'Grupo' justo al lado de 'Municipio'
if 'Municipio' in columnas:
    indice = columnas.index('Municipio')
    columnas.insert(indice + 1, 'Grupo')
else:
    columnas.insert(3, 'Grupo')

df_final = df_rest[columnas]

# Guardamos el resultado en un nuevo archivo independiente
df_final.to_csv(RUTA_NUEVO_ARCHIVO, sep=';', index=False)

print("\n✅ ¡Clasificación completada!")
print(f"📊 Total de restaurantes procesados: {len(df_final)}")
print(f"💾 El nuevo archivo enriquecido se ha guardado en: '{RUTA_NUEVO_ARCHIVO}'")