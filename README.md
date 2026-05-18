# Málaga Gastro-Locator — Sitio estático para GitHub Pages

Este repositorio contiene un generador simple que transforma el CSV (si existe) en una página estática desplegada en GitHub Pages.

- Ejecuta `python build_site.py` para generar `site/index.html` y `site/data.json`.
- El workflow `.github/workflows/pages.yml` construye y despliega automáticamente la carpeta `site` a GitHub Pages cuando hay push a `main`.

Notas:
- Si ya tienes una página de usuario `username.github.io`, este despliegue publicará el sitio como página de proyecto en `https://username.github.io/<repo>`.
- No necesitas renombrar el repo ni hacerlo público si quieres usar Pages en repositorio público; Pages funciona con repos privados también según configuración, pero es más sencillo si el repo es público.
