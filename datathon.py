import os
import pandas as pd

CSV_PATH = "data/Economia-y-empleo - Economia y empleo.csv"


def _fallback_data():
    datos_malaga = {
        'Distrito': ['Centro', 'Este (El Palo/Pedregalejo)', 'Ciudad Jardín', 'Bailén-Miraflores',
                     'Palma-Palmilla', 'Cruz de Humilladero', 'Carretera de Cádiz', 'Churriana',
                     'Campanillas', 'Puerto de la Torre', 'Teatinos-Universidad'],
        'Lat': [36.7213, 36.7236, 36.7460, 36.7300, 36.7400, 36.7150, 36.6974, 36.6667, 36.7369, 36.7500, 36.7179],
        'Lon': [-4.4214, -4.3621, -4.4260, -4.4400, -4.4300, -4.4450, -4.4447, -4.5000, -4.5500, -4.4800, -4.4744],
        'Renta_Media_Euros': [29000, 36000, 20000, 21000, 16000, 23000, 24000, 25000, 22000, 28000, 27500]
    }
    return pd.DataFrame(datos_malaga)


def load_data(csv_path=CSV_PATH):
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            required = ['Distrito', 'Lat', 'Lon', 'Renta_Media_Euros']
            if all(c in df.columns for c in required):
                return df
            print("CSV found but missing required columns; using sample fallback data.")
        except Exception:
            print("Error reading CSV; using sample fallback data.")

    return _fallback_data()


def categorize(renta):
    if renta < 22000:
        return "Renta Baja"
    if renta <= 28000:
        return "Renta Media"
    return "Renta Alta"


def prepare_data(csv_path=CSV_PATH):
    df = load_data(csv_path)
    df = df.rename(columns={c: c.strip() for c in df.columns})

    required = ['Distrito', 'Lat', 'Lon', 'Renta_Media_Euros']
    for col in required:
        if col not in df.columns:
            raise SystemExit(f"CSV missing required column: {col}")

    df['Categoria'] = df['Renta_Media_Euros'].apply(categorize)
    return df


def run_streamlit():
    import streamlit as st
    import folium
    from streamlit_folium import st_folium

    st.set_page_config(page_title="Málaga Gastro-Locator", layout="wide")
    st.title("📍 Málaga Gastro-Locator: Encuentra tu zona ideal")
    st.markdown("Analiza las mejores zonas de Málaga para abrir tu restaurante según el poder adquisitivo de tu cliente objetivo.")

    df = prepare_data()

    st.sidebar.header("Filtros del Negocio")
    perfil_cliente = st.sidebar.radio(
        "Selecciona el perfil de renta de tu cliente objetivo:",
        ("Renta Baja", "Renta Media", "Renta Alta")
    )

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

    mapa_malaga = folium.Map(location=[36.7213, -4.4214], zoom_start=12, tiles="CartoDB positron")

    for _, row in df_filtrado.iterrows():
        folium.CircleMarker(
            location=[row['Lat'], row['Lon']],
            radius=15,
            popup=f"<b>{row['Distrito']}</b><br>Renta: {row['Renta_Media_Euros']}€",
            color=color_marcador,
            fill=True,
            fill_color=color_marcador,
            fill_opacity=0.6
        ).add_to(mapa_malaga)

    st_folium(mapa_malaga, width=800, height=500)


if __name__ == '__main__':
    run_streamlit()