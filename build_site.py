import os
import json
import pandas as pd

OUT_DIR = "site"
OUT_DATA = os.path.join(OUT_DIR, "data.json")
OUT_INDEX = os.path.join(OUT_DIR, "index.html")
TEMPLATE_PATH = os.path.join(OUT_DIR, "template.html")
SOURCE_CSV = "cruce_potencial.csv"

REQUIRED_COLS = {
    "municipio",
    "poblacion",
    "num_restaurantes",
    "rest_por_1000hab",
    "potencial",
    "categoria_potencial",
    "densidad_pob_norm",
    "lat",
    "lon",
}


def load_cruce_data():
    if os.path.exists(SOURCE_CSV):
        df = pd.read_csv(SOURCE_CSV)
    else:
        try:
            import gastro_locator

            df = gastro_locator.generate_csvs()
        except Exception as exc:
            raise SystemExit(
                f"Missing {SOURCE_CSV} and failed to generate it."
            ) from exc

    missing = REQUIRED_COLS.difference(df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise SystemExit(f"Source data missing required columns: {missing_list}")

    df = df.sort_values("potencial", ascending=False).reset_index(drop=True)

    numeric_cols = [
        "poblacion",
        "num_restaurantes",
        "rest_por_1000hab",
        "potencial",
        "densidad_pob_norm",
        "lat",
        "lon",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["poblacion"] = df["poblacion"].fillna(0).astype(int)
    df["num_restaurantes"] = df["num_restaurantes"].fillna(0).astype(int)
    if "anio" in df.columns:
        df["anio"] = pd.to_numeric(df["anio"], errors="coerce").fillna(0).astype(int)

    return df


def build():
    df = load_cruce_data()

    os.makedirs(OUT_DIR, exist_ok=True)

    data = df.to_dict(orient='records')
    with open(OUT_DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if not os.path.exists(TEMPLATE_PATH):
        raise SystemExit(f"Missing template file: {TEMPLATE_PATH}")

    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    with open(OUT_INDEX, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Wrote {OUT_INDEX} and {OUT_DATA}")


if __name__ == '__main__':
    build()
