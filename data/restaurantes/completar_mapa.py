import csv
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from geopy.geocoders import Nominatim

# ==========================================
# CONFIGURACIÓN DE RENDIMIENTO
# ==========================================
NUM_THREADS = 3              # Número de hilos simultáneos (Aumenta o disminuye según veas)
FRECUENCIA_AUTOGUARDADO = 20   # Guardar en disco cada X restaurantes procesados
archivo_origen = 'restaurantes_bruto.csv'  
archivo_destino = 'restaurantes_multithread_malaga.csv'
# ==========================================

# Inicializador de bloqueos para proteger la escritura en el archivo
file_lock = Lock()
contador_global = 0

print(f"=====================================================================")
# 
print(f" LANZANDO SCRIPT EN MODO MULTIHILO TRABAJANDO CON {NUM_THREADS} THREADS")
print(f"=====================================================================")

# Crear cabecera si el archivo no existe
if not os.path.exists(archivo_destino):
    with open(archivo_destino, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow([
            'Nombre', 'Codigo_Postal', 'Calle', 'Municipio', 'Distrito', 
            'Latitud', 'Longitud', 'Provincia', 'Pais', 'Tipo_Cocina', 'Sitio_Web', 'Direccion_Completa'
        ])

# Función individual que ejecutará cada Hilo independiente
def procesar_restaurante(fila_csv, thread_id):
    if not fila_csv or not fila_csv[0].strip():
        return None
        
    nombre = fila_csv[0].strip()
    cp = fila_csv[1].strip() if len(fila_csv) > 1 else ""
    calle = fila_csv[2].strip() if len(fila_csv) > 2 else ""
    
    # Cada hilo se identifica con su propio User-Agent para no saturar las cabeceras
    geolocator = Nominatim(user_agent=f"multithread_malaga_agent_{thread_id}")
    
    latitud, longitud, provincia, pais, direccion_completa = "", "", "", "", ""
    municipio, distrito, tipo_cocina, sitio_web = "", "", "", ""
    
    try:
        termino_busqueda = f"{nombre}, Malaga, Spain"
        location = geolocator.geocode(termino_busqueda, addressdetails=True, timeout=15)
        
        if location:
            latitud = location.latitude
            longitud = location.longitude
            direccion_completa = location.address
            address = location.raw.get('address', {})
            
            if not cp: cp = address.get('postcode', '')
            if not calle: calle = address.get('road', address.get('pedestrian', address.get('suburb', '')))
            
            municipio = address.get('town', address.get('city', address.get('municipality', address.get('village', ''))))
            if not municipio and address.get('county') == 'Málaga':
                municipio = 'Málaga'
            
            distrito = address.get('suburb', address.get('city_district', address.get('neighbourhood', '')))
            provincia = address.get('county', 'Málaga')
            pais = address.get('country', 'España')
            
            extratags = location.raw.get('extratags', {})
            tipo_cocina = extratags.get('cuisine', address.get('cuisine', 'No especificado'))
            sitio_web = extratags.get('website', extratags.get('contact:website', extratags.get('facebook', 'No disponible')))
            
            print(f"[Hilo-{thread_id}][ÉXITO] Encontrado: {nombre}")
        else:
            print(f"[Hilo-{thread_id}][VACÍO] No localizado en mapa: {nombre}")
            
    except Exception as e:
        print(f"[Hilo-{thread_id}][ERROR] Fallo en '{nombre}': {e}")
        
    # Obligamos al hilo a esperar un poco antes de su siguiente consulta para no asfixiar al servidor
    time.sleep(1.5)
    
    return [nombre, cp, calle, municipio, distrito, latitud, longitud, provincia, pais, tipo_cocina, sitio_web, direccion_completa]


# Bloque principal para coordinar los hilos
def main():
    global contador_global
    
    # Leer todas las filas del archivo de origen y cargarlas en memoria
    with open(archivo_origen, mode='r', encoding='utf-8') as infile:
        reader = csv.reader(infile, delimiter=',')
        next(reader, None) # Saltar cabecera
        filas = list(reader)

    print(f"Cargados {len(filas)} restaurantes en cola. Repartiendo el trabajo...")

    # Abrimos el archivo de salida en modo Append ('a') para añadir datos de forma continua
    with open(archivo_destino, mode='a', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=';')
        
        # Iniciamos el pool de hilos de tu máquina
        with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            # Asignamos las tareas pasándole a cada restaurante un ID de hilo (del 1 al NUM_THREADS)
            futuros = {executor.submit(procesar_restaurante, fila, (i % NUM_THREADS) + 1): fila for i, fila in enumerate(filas)}
            
            # Conforme los hilos van terminando sus tareas...
            for futuro in as_completed(futuros):
                resultado = futuro.result()
                
                if resultado:
                    # Ponemos el cerrojo (Lock) para asegurar que solo un hilo escribe a la vez y no se mezclen letras
                    with file_lock:
                        writer.writerow(resultado)
                        contador_global += 1
                        
                        # Sistema de autoguardado periódico coordinado
                        if contador_global % FRECUENCIA_AUTOGUARDADO == 0:
                            outfile.flush()
                            os.fsync(outfile.fileno())
                            print(f"--> [DISCO] {contador_global} filas consolidadas de forma segura en el almacenamiento.")

if __name__ == '__main__':
    start_time = time.time()
    main()
    print(f"\n=====================================================================")
    print(f" ¡PROCESO COMPLETADO EN {round((time.time() - start_time)/60, 2)} MINUTOS!")
    print(f"=====================================================================")