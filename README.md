# Kindle: pogoda + kalendarz (Wrocław)

GitHub Actions co 30 min generuje `dashboard.png` (600×800) i publikuje go na GitHub Pages.
Kindle (po jailbreaku, rozszerzenie KUAL „Pogoda i kalendarz”) pobiera obrazek i go wyświetla.

- Pogoda: Open-Meteo (bez klucza API)
- Zmiana miasta: `CITY`, `LAT`, `LON` w `generate.py`
- Podgląd lokalnie: `pip install pillow && python generate.py podglad.png`
