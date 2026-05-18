import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Málaga Gastro-Locator", layout="wide")
st.title("📍 Málaga Gastro-Locator: Encuentra tu zona ideal")
st.markdown("Analiza las mejores zonas de Málaga para abrir tu restaurante según el poder adquisitivo de tu cliente objetivo.")

# --- 2. DATOS (Simulados para la Datathon) ---
# Aquí es donde deberéis cargar vuestro CSV real cuando lo tengáis
# Ejemplo: df = pd.read_csv('renta_barrios_malaga.csv')
datos_malaga = {
    'Distrito': ['Centro', 'Este (El Palo/Pedregalejo)', 'Ciudad Jardín', 'Bailén-Miraflores', 
                 'Palma-Palmilla', 'Cruz de Humilladero', 'Carretera de Cádiz', 'Churriana', 
                 'Campanillas', 'Puerto de la Torre', 'Teatinos-Universidad'],
    'Lat': [36.7213, 36.7236, 36.7460, 36.7300, 36.7400, 36.7150, 36.6974, 36.6667, 36.7369, 36.7500, 36.7179],
    'Lon': [-4.4214, -4.3621, -4.4260, -4.4400, -4.4300, -4.4450, -4.4447, -4.5000, -4.5500, -4.4800, -4.4744],
    'Renta_Media_Euros': [29000, 36000, 20000, 21000, 16000, 23000, 24000, 25000, 22000, 28000, 27500]
}
df = pd.DataFrame(datos_malaga)

# --- 3. INTERFAZ DE USUARIO ---
st.sidebar.header("Filtros del Negocio")
perfil_cliente = st.sidebar.radio(
    "Selecciona el perfil de renta de tu cliente objetivo:",
    ("Renta Baja", "Renta Media", "Renta Alta")
)

# --- 4. LÓGICA DE NEGOCIO ---
# Definimos qué consideramos cada nivel de renta (Ajustar según datos reales)
if perfil_cliente == "Renta Baja":
    df_filtrado = df[df['Renta_Media_Euros'] < 22000]
    color_marcador = 'blue'
elif perfil_cliente == "Renta Media":
    df_filtrado = df[(df['Renta_Media_Euros'] >= 22000) & (df['Renta_Media_Euros'] <= 28000)]
    color_marcador = 'orange'
else:
    df_filtrado = df[df['Renta_Media_Euros'] > 28000]
    color_marcador = 'red'

st.subheader(f"Distritos recomendados para público de {perfil_cliente}")
st.dataframe(df_filtrado[['Distrito', 'Renta_Media_Euros']].style.format({"Renta_Media_Euros": "{} €"}))

# --- 5. MAPA INTERACTIVO ---
# Centramos el mapa en Málaga capital
mapa_malaga = folium.Map(location=[36.7213, -4.4214], zoom_start=12, tiles="CartoDB positron")

# Añadimos los distritos recomendados al mapa
for index, row in df_filtrado.iterrows():
    folium.CircleMarker(
        location=[row['Lat'], row['Lon']],
        radius=15,
        popup=f"<b>{row['Distrito']}</b><br>Renta: {row['Renta_Media_Euros']}€",
        color=color_marcador,
        fill=True,
        fill_color=color_marcador,
        fill_opacity=0.6
    ).add_to(mapa_malaga)

# Mostramos el mapa en Streamlit
st_folium(mapa_malaga, width=800, height=500)