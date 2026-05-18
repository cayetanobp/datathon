import os
import json
import pandas as pd

CSV_PATH = "Economia-y-empleo - Economia y empleo.csv"
OUT_DIR = "site"
OUT_DATA = os.path.join(OUT_DIR, "data.json")
OUT_INDEX = os.path.join(OUT_DIR, "index.html")


def load_data():
  if os.path.exists(CSV_PATH):
    try:
      df = pd.read_csv(CSV_PATH)
      # Expect columns: Distrito, Lat, Lon, Renta_Media_Euros
      required = ['Distrito', 'Lat', 'Lon', 'Renta_Media_Euros']
      if all(c in df.columns for c in required):
        return df
      else:
        print("CSV found but missing required columns; using sample fallback data.")
    except Exception:
      print("Error reading CSV; using sample fallback data.")

  # Fallback sample data (same as original Streamlit example)
    datos_malaga = {
        'Distrito': ['Centro', 'Este (El Palo/Pedregalejo)', 'Ciudad Jardín', 'Bailén-Miraflores',
                     'Palma-Palmilla', 'Cruz de Humilladero', 'Carretera de Cádiz', 'Churriana',
                     'Campanillas', 'Puerto de la Torre', 'Teatinos-Universidad'],
        'Lat': [36.7213, 36.7236, 36.7460, 36.7300, 36.7400, 36.7150, 36.6974, 36.6667, 36.7369, 36.7500, 36.7179],
        'Lon': [-4.4214, -4.3621, -4.4260, -4.4400, -4.4300, -4.4450, -4.4447, -4.5000, -4.5500, -4.4800, -4.4744],
        'Renta_Media_Euros': [29000, 36000, 20000, 21000, 16000, 23000, 24000, 25000, 22000, 28000, 27500]
    }
    return pd.DataFrame(datos_malaga)


def categorize(renta):
    if renta < 22000:
        return "Renta Baja"
    if renta <= 28000:
        return "Renta Media"
    return "Renta Alta"


def build():
    df = load_data()
    df = df.rename(columns={c: c.strip() for c in df.columns})

    # Ensure required columns exist
    required = ['Distrito', 'Lat', 'Lon', 'Renta_Media_Euros']
    for col in required:
        if col not in df.columns:
            raise SystemExit(f"CSV missing required column: {col}")

    df['Categoria'] = df['Renta_Media_Euros'].apply(categorize)

    os.makedirs(OUT_DIR, exist_ok=True)

    data = df.to_dict(orient='records')
    with open(OUT_DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Minimal HTML + Leaflet frontend that reads data.json
    html = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Málaga Gastro-Locator (estático)</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="" crossorigin=""/>
  <style>body {{ font-family: Arial, sans-serif; margin:0; }} #map {{ height:60vh; }} .controls {{ padding:10px; }}</style>
</head>
<body>
  <header style="padding:12px; background:#f7f7f7;"><h1>📍 Málaga Gastro-Locator</h1><p>Versión estática desplegada por GitHub Pages.</p></header>
  <div class="controls">
    <label>Perfil cliente: <select id="perfil"><option value="Todas">Todas</option><option>Renta Baja</option><option>Renta Media</option><option>Renta Alta</option></select></label>
    <button id="reset">Mostrar todos</button>
  </div>
  <div id="map"></div>
  <section style="padding:12px;"><h2>Distritos</h2><table id="table" border="1" cellpadding="6"></table></section>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    async function load(){
      const res = await fetch('data.json');
      const data = await res.json();
      const map = L.map('map').setView([36.7213, -4.4214], 12);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19}).addTo(map);

      const markers = [];
      function colorFor(cat){
        return cat === 'Renta Baja' ? 'blue' : (cat === 'Renta Media' ? 'orange' : 'red');
      }

      function renderTable(items){
        const table = document.getElementById('table');
        table.innerHTML = '<tr><th>Distrito</th><th>Renta</th><th>Categoria</th></tr>' + items.map(r=>`<tr><td>${r.Distrito}</td><td>${r.Renta_Media_Euros} €</td><td>${r.Categoria}</td></tr>`).join('');
      }

      data.forEach(r=>{
        const m = L.circleMarker([r.Lat, r.Lon], {radius:10, color: colorFor(r.Categoria), fill:true, fillOpacity:0.6})
          .bindPopup(`<b>${r.Distrito}</b><br>Renta: ${r.Renta_Media_Euros} €`)
          .addTo(map);
        markers.push({marker:m, record:r});
      });

      function filterBy(cat){
        const items = cat === 'Todas' ? data : data.filter(d=>d.Categoria===cat);
        markers.forEach(x=>{ if(items.indexOf(x.record)===-1) map.removeLayer(x.marker); else x.marker.addTo(map); });
        renderTable(items);
      }

      document.getElementById('perfil').addEventListener('change', e=>filterBy(e.target.value));
      document.getElementById('reset').addEventListener('click', ()=>{ document.getElementById('perfil').value='Todas'; filterBy('Todas'); });

      renderTable(data);
    }
    load();
  </script>
</body>
</html>
"""

    with open(OUT_INDEX, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Wrote {OUT_INDEX} and {OUT_DATA}")


if __name__ == '__main__':
    build()
