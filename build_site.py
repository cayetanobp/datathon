import os
import json
import datathon

OUT_DIR = "site"
OUT_DATA = os.path.join(OUT_DIR, "data.json")
OUT_INDEX = os.path.join(OUT_DIR, "index.html")
TEMPLATE_PATH = os.path.join(OUT_DIR, "template.html")


def build():
    df = datathon.prepare_data()

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
