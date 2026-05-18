"""
Gastro-Locator: Cruce de densidad de población y densidad de licencias de restauración.
Genera 3 CSVs normalizados y un mapa de calor interactivo con Streamlit.
"""

import os
import pandas as pd
import numpy as np

# ─── Rutas ────────────────────────────────────────────────────────────────────
REST_CSV   = "restaurantes_con_grupo_cp.csv"
POB_XLSX   = "Poblacion-Diciembre-2024.xlsx"
OUT_REST   = "restaurantes_normalizado.csv"
OUT_POB    = "poblacion_normalizada.csv"
OUT_CRUCE  = "cruce_potencial.csv"

# ─── Mapeo municipio (XLSX) → grupo normalizado ────────────────────────────────
MUNICIPIO_TO_GRUPO = {
    "Alhaurín de la Torre": "alhaurindelatorre",
    "Alhaurín el Grande":   "alhaurinelgrande",
    "Almogía":              "almogia",
    "Benalmádena":          "benalmadena",
    "Cártama":              "cartama",
    "Casabermeja":          "casabermeja",
    "Colmenar":             "colmenar",
    "Fuengirola":           "fuengirola",
    "Málaga":               "malaga",
    "Mijas":                "mijas",
    "Pizarra":              "pizarra",
    "Rincón de la Victoria":"rincondelavictoria",
    "Totalán":              "totalan",
    "Torremolinos":         "torremolinos",
    "Álora":                "alora",
    "Coín":                 "coin",
}

# Coordenadas centroide de referencia por grupo (fallback si CSV no tiene datos suficientes)
COORDS_REF = {
    "malaga":               (36.7213, -4.4214),
    "benalmadena":          (36.5986, -4.5153),
    "torremolinos":         (36.6213, -4.4997),
    "fuengirola":           (36.5404, -4.6252),
    "mijas":                (36.5963, -4.6377),
    "rincondelavictoria":   (36.7195, -4.2481),
    "alhaurindelatorre":    (36.6702, -4.5490),
    "colmenar":             (36.9139, -4.3316),
    "coin":                 (36.6600, -4.7590),
    "alhaurinelgrande":     (36.6433, -4.6890),
    "almogia":              (36.8290, -4.5330),
    "alora":                (36.8217, -4.6971),
    "cartama":              (36.7200, -4.6368),
    "totalan":              (36.7730, -4.3080),
    "casabermeja":          (36.8580, -4.4250),
    "pizarra":              (36.7700, -4.7050),
}


def load_restaurantes(path=REST_CSV):
    df = pd.read_csv(path, on_bad_lines="skip", sep=None, engine="python")
    df.columns = [c.strip() for c in df.columns]
    # Solo filas con grupo asignado
    df = df[df["Grupo"].notna()].copy()
    df["Grupo"] = df["Grupo"].str.strip().str.lower()
    df["Latitud"]  = pd.to_numeric(df["Latitud"],  errors="coerce")
    df["Longitud"] = pd.to_numeric(df["Longitud"], errors="coerce")
    return df


def build_restaurantes_norm(df_rest):
    grp = df_rest.groupby("Grupo").agg(
        num_restaurantes=("Nombre", "count"),
        lat=("Latitud",  "mean"),
        lon=("Longitud", "mean"),
    ).reset_index()

    # Rellenar coordenadas faltantes con referencia
    for idx, row in grp.iterrows():
        if pd.isna(row["lat"]) or pd.isna(row["lon"]):
            coords = COORDS_REF.get(row["Grupo"])
            if coords:
                grp.at[idx, "lat"] = coords[0]
                grp.at[idx, "lon"] = coords[1]

    total = grp["num_restaurantes"].sum()
    grp["pct_restaurantes"] = (grp["num_restaurantes"] / total * 100).round(2)
    grp["densidad_rest_norm"] = (
        (grp["num_restaurantes"] - grp["num_restaurantes"].min()) /
        (grp["num_restaurantes"].max() - grp["num_restaurantes"].min())
    ).round(4)
    return grp.rename(columns={"Grupo": "grupo"})


def load_poblacion(path=POB_XLSX):
    df_raw = pd.read_excel(path, sheet_name="Población", header=None)

    # Fila 31: cabeceras municipios (col 2 en adelante)
    header_row = df_raw.iloc[31]
    municipios = header_row[2:].dropna().tolist()

    # Buscar último año con datos (fila con valor numérico en col 1)
    data_rows = df_raw[df_raw.iloc[:, 1].apply(lambda x: str(x).replace(".0","").isdigit())]
    # Tomar solo el bloque de municipios (filas 32-55 aprox)
    data_block = data_rows[(data_rows.index >= 32) & (data_rows.index <= 55)]
    last_row = data_block.iloc[-1]  # año más reciente

    anio = int(last_row.iloc[1])
    values = last_row.iloc[2:2+len(municipios)].values

    df_pob = pd.DataFrame({
        "municipio": municipios,
        f"poblacion_{anio}": pd.to_numeric(values, errors="coerce"),
    })
    df_pob["anio"] = anio
    return df_pob, anio


def build_poblacion_norm(df_pob, anio):
    col = f"poblacion_{anio}"
    df = df_pob[["municipio", col, "anio"]].copy()
    df = df[df[col].notna()]
    df["grupo"] = df["municipio"].map(MUNICIPIO_TO_GRUPO)
    df = df[df["grupo"].notna()]
    df = df.rename(columns={col: "poblacion"})

    total = df["poblacion"].sum()
    df["pct_poblacion"] = (df["poblacion"] / total * 100).round(2)
    df["densidad_pob_norm"] = (
        (df["poblacion"] - df["poblacion"].min()) /
        (df["poblacion"].max() - df["poblacion"].min())
    ).round(4)
    return df[["grupo", "municipio", "anio", "poblacion", "pct_poblacion", "densidad_pob_norm"]]


def build_cruce(df_rest_norm, df_pob_norm):
    df = pd.merge(df_pob_norm, df_rest_norm, on="grupo", how="left")
    df["num_restaurantes"] = df["num_restaurantes"].fillna(0).astype(int)

    # Restaurantes por cada 1.000 habitantes
    df["rest_por_1000hab"] = (df["num_restaurantes"] / df["poblacion"] * 1000).round(4)

    # Excluir Malaga del dataset final
    df = df[df["grupo"].fillna("").str.lower() != "malaga"].copy()

    # Normalizar densidad de restauración (0=ninguno, 1=máximo)
    min_d, max_d = df["rest_por_1000hab"].min(), df["rest_por_1000hab"].max()
    if max_d > min_d:
        df["densidad_rest_norm"] = ((df["rest_por_1000hab"] - min_d) / (max_d - min_d)).round(4)
    else:
        df["densidad_rest_norm"] = 0.0

    # Potencial = zona poco saturada + alta población
    # 60 % peso en baja densidad de restauración, 40 % en alta población
    df["potencial"] = (
        (1 - df["densidad_rest_norm"]) * 0.60 +
        df["densidad_pob_norm"]        * 0.40
    ).round(4)

    # Categoría
    def categorize(p):
        if p > 0.5:
            return "Alto Potencial"
        if p >= 0.3:
            return "Potencial Medio"
        return "Potencial Bajo"

    df["categoria_potencial"] = df["potencial"].apply(categorize)

    # Añadir coordenadas de referencia donde falten
    for idx, row in df.iterrows():
        if pd.isna(row.get("lat")):
            coords = COORDS_REF.get(row["grupo"])
            if coords:
                df.at[idx, "lat"] = coords[0]
                df.at[idx, "lon"] = coords[1]

    cols = [
        "grupo", "municipio", "anio", "poblacion", "pct_poblacion",
        "num_restaurantes", "pct_restaurantes", "rest_por_1000hab",
        "densidad_pob_norm", "densidad_rest_norm", "potencial",
        "categoria_potencial", "lat", "lon",
    ]
    # pct_restaurantes puede no estar si grupo no tenía restaurantes
    if "pct_restaurantes" not in df.columns:
        df["pct_restaurantes"] = 0.0
    df["pct_restaurantes"] = df["pct_restaurantes"].fillna(0.0)

    return df[cols].sort_values("potencial", ascending=False).reset_index(drop=True)


def generate_csvs():
    df_rest  = load_restaurantes()
    rest_n   = build_restaurantes_norm(df_rest)
    df_pob, anio = load_poblacion()
    pob_n    = build_poblacion_norm(df_pob, anio)
    cruce    = build_cruce(rest_n, pob_n)

    rest_n.to_csv(OUT_REST,  index=False, encoding="utf-8-sig")
    pob_n.to_csv(OUT_POB,   index=False, encoding="utf-8-sig")
    cruce.to_csv(OUT_CRUCE, index=False, encoding="utf-8-sig")

    print(f"✅ {OUT_REST}  ({len(rest_n)} grupos)")
    print(f"✅ {OUT_POB}   ({len(pob_n)} grupos)")
    print(f"✅ {OUT_CRUCE} ({len(cruce)} grupos)")
    return cruce


# ─── Streamlit ────────────────────────────────────────────────────────────────
def run_streamlit():
    import streamlit as st
    import folium
    from streamlit_folium import st_folium

    st.set_page_config(page_title="Gastro-Locator Málaga", layout="wide")
    st.title("🗺️ Gastro-Locator: Zonas con Potencial de Restauración")
    st.markdown(
        "Cruce de **densidad de población** y **densidad de licencias de restauración** "
        "por zona. Las zonas con mayor potencial combinan alta población y baja saturación de restaurantes."
    )

    # Generar/cargar datos
    if not os.path.exists(OUT_CRUCE):
        with st.spinner("Procesando datos..."):
            df = generate_csvs()
    else:
        df = pd.read_csv(OUT_CRUCE)

    # ─── Sidebar ──────────────────────────────────────────────────────────────
    st.sidebar.header("⚙️ Filtros")
    categorias = st.sidebar.multiselect(
        "Categoría de potencial",
        options=["Alto Potencial", "Potencial Medio", "Potencial Bajo"],
        default=["Alto Potencial", "Potencial Medio"],
    )
    min_pob = st.sidebar.slider(
        "Población mínima",
        min_value=0,
        max_value=int(df["poblacion"].max()),
        value=0,
        step=1000,
        format="%d hab.",
    )

    df_f = df[
        df["categoria_potencial"].isin(categorias) &
        (df["poblacion"] >= min_pob)
    ]

    # ─── KPIs ─────────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Zonas analizadas", len(df))
    col2.metric("Zonas filtradas",  len(df_f))
    col3.metric("Restaurantes totales", int(df["num_restaurantes"].sum()))
    anio_datos = int(df["anio"].iloc[0]) if "anio" in df.columns else "—"
    col4.metric("Año datos población", anio_datos)

    # ─── Tabla ────────────────────────────────────────────────────────────────
    st.subheader("📋 Ranking de Zonas por Potencial")
    tabla_cols = ["municipio", "poblacion", "num_restaurantes",
                  "rest_por_1000hab", "potencial", "categoria_potencial"]
    st.dataframe(
        df_f[tabla_cols].style
            .format({
                "poblacion":         "{:,.0f}",
                "rest_por_1000hab":  "{:.2f}",
                "potencial":         "{:.3f}",
            })
            .background_gradient(subset=["potencial"], cmap="RdYlGn"),
        use_container_width=True,
        height=300,
    )

    # ─── Mapa ─────────────────────────────────────────────────────────────────
    st.subheader("🔥 Mapa de Calor de Potencial")

    COLOR_MAP = {
        "Alto Potencial":  ("#2ECC71", "green"),
        "Potencial Medio": ("#F39C12", "orange"),
        "Potencial Bajo":  ("#E74C3C", "red"),
    }

    mapa = folium.Map(location=[36.72, -4.50], zoom_start=10, tiles="CartoDB positron")

    for _, row in df_f.iterrows():
        if pd.isna(row["lat"]) or pd.isna(row["lon"]):
            continue
        fill_hex, _ = COLOR_MAP.get(row["categoria_potencial"], ("#888888", "gray"))
        radius = 10 + row["densidad_pob_norm"] * 25  # círculo proporcional a población

        popup_html = f"""
        <div style='font-family:Arial; min-width:200px'>
          <b style='font-size:14px'>{row['municipio']}</b><br>
          <hr style='margin:4px 0'>
          🏷️ <b>{row['categoria_potencial']}</b><br>
          👥 Población: <b>{int(row['poblacion']):,}</b><br>
          🍽️ Restaurantes: <b>{int(row['num_restaurantes'])}</b><br>
          📊 Rest/1.000 hab: <b>{row['rest_por_1000hab']:.2f}</b><br>
          ⭐ Potencial: <b>{row['potencial']:.3f}</b>
        </div>
        """

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{row['municipio']} — {row['categoria_potencial']}",
            color=fill_hex,
            fill=True,
            fill_color=fill_hex,
            fill_opacity=0.70,
            weight=2,
        ).add_to(mapa)

    # Leyenda
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
                background:white;padding:12px 16px;border-radius:8px;
                border:1px solid #ccc;font-family:Arial;font-size:13px">
      <b>Potencial de Restauración</b><br>
      <span style="color:#2ECC71">●</span> Alto Potencial<br>
      <span style="color:#F39C12">●</span> Potencial Medio<br>
      <span style="color:#E74C3C">●</span> Potencial Bajo<br>
      <small>Tamaño ∝ Población</small>
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(legend_html))

    st_folium(mapa, width="100%", height=550)

    # ─── Descargar CSVs ───────────────────────────────────────────────────────
    st.subheader("📥 Descargar Datasets Normalizados")
    c1, c2, c3 = st.columns(3)

    def csv_btn(col, path, label):
        if os.path.exists(path):
            with open(path, "rb") as f:
                col.download_button(label, f, file_name=os.path.basename(path),
                                    mime="text/csv", use_container_width=True)

    csv_btn(c1, OUT_CRUCE, "⬇️ cruce_potencial.csv")
    csv_btn(c2, OUT_REST,  "⬇️ restaurantes_normalizado.csv")
    csv_btn(c3, OUT_POB,   "⬇️ poblacion_normalizada.csv")

    st.caption(
        "**Metodología:** Potencial = (1 − densidad_restaurantes_norm) × 0,6  +  "
        "densidad_población_norm × 0,4  |  Datos: Padrón Municipal · Licencias apertura Málaga"
    )


if __name__ == "__main__":
    # Si se llama directamente, solo genera los CSVs
    import sys
    if "streamlit" in sys.modules or any("streamlit" in arg for arg in sys.argv):
        run_streamlit()
    else:
        cruce = generate_csvs()
        print("\n=== Vista previa cruce_potencial.csv ===")
        print(cruce[["municipio", "poblacion", "num_restaurantes",
                      "rest_por_1000hab", "potencial", "categoria_potencial"]].to_string(index=False))
