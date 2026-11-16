#!/usr/bin/env python3
"""Generuje dashboard.png (600x800, skala szarości) dla Kindle:
data + kalendarz miesiąca + pogoda (Open-Meteo, bez klucza API)."""
import calendar
import datetime as dt
import json
import math
import os
import sys
import urllib.request
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

# ---- Ustawienia ----
CITY = "Wrocław"
LAT, LON = 51.1079, 17.0385
TZ = ZoneInfo("Europe/Warsaw")
W, H = 600, 800
OUT = sys.argv[1] if len(sys.argv) > 1 else "dashboard.png"
HERE = os.path.dirname(os.path.abspath(__file__))

BLACK, WHITE, GRAY, LIGHT = 0, 255, 110, 200

DAYS = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
DAYS_SHORT = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"]
MONTHS_GEN = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca",
              "sierpnia", "września", "października", "listopada", "grudnia"]
MONTHS_NOM = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec",
              "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]


def font(size, bold=False, cond=False):
    name = "DejaVuSansCondensed-Bold.ttf" if cond else ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    return ImageFont.truetype(os.path.join(HERE, "fonts", name), size)


# ---- Pogoda ----
def fetch_weather():
    url = ("https://api.open-meteo.com/v1/forecast"
           f"?latitude={LAT}&longitude={LON}"
           "&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,is_day"
           "&hourly=temperature_2m,weather_code,precipitation_probability,is_day"
           "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset"
           "&timezone=Europe%2FWarsaw&forecast_days=5")
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.load(r)


def describe(code):
    table = {
        0: ("Bezchmurnie", "sun"), 1: ("Przeważnie słonecznie", "sun"),
        2: ("Częściowe zachmurzenie", "partly"), 3: ("Pochmurno", "cloud"),
        45: ("Mgła", "fog"), 48: ("Szadź i mgła", "fog"),
        51: ("Lekka mżawka", "drizzle"), 53: ("Mżawka", "drizzle"), 55: ("Gęsta mżawka", "drizzle"),
        56: ("Marznąca mżawka", "drizzle"), 57: ("Marznąca mżawka", "drizzle"),
        61: ("Słaby deszcz", "rain"), 63: ("Deszcz", "rain"), 65: ("Ulewa", "rain"),
        66: ("Marznący deszcz", "rain"), 67: ("Marznący deszcz", "rain"),
        71: ("Słaby śnieg", "snow"), 73: ("Śnieg", "snow"), 75: ("Intensywny śnieg", "snow"),
        77: ("Krupa śnieżna", "snow"),
        80: ("Przelotny deszcz", "showers"), 81: ("Przelotne opady", "showers"),
        82: ("Gwałtowne ulewy", "showers"),
        85: ("Przelotny śnieg", "snow"), 86: ("Intensywny śnieg", "snow"),
        95: ("Burza", "storm"), 96: ("Burza z gradem", "storm"), 99: ("Burza z gradem", "storm"),
    }
    return table.get(code, ("—", "cloud"))


# ---- Ikony rysowane wektorowo ----
def draw_sun(d, cx, cy, r, fill=BLACK):
    d.ellipse([cx - r * .45, cy - r * .45, cx + r * .45, cy + r * .45], outline=fill, width=max(2, int(r * .09)))
    for i in range(8):
        a = i * math.pi / 4
        x1, y1 = cx + math.cos(a) * r * .62, cy + math.sin(a) * r * .62
        x2, y2 = cx + math.cos(a) * r * .9, cy + math.sin(a) * r * .9
        d.line([x1, y1, x2, y2], fill=fill, width=max(2, int(r * .09)))


def draw_moon(d, cx, cy, r):
    d.ellipse([cx - r * .55, cy - r * .55, cx + r * .55, cy + r * .55], fill=BLACK)
    d.ellipse([cx - r * .3, cy - r * .75, cx + r * .75, cy + r * .3], fill=WHITE)


def draw_cloud(d, cx, cy, r, fill=WHITE, outline=BLACK):
    w = max(2, int(r * .08))
    parts = [
        (cx - r * .55, cy - r * .05, cx + r * .05, cy + r * .5),
        (cx - r * .3, cy - r * .45, cx + r * .35, cy + r * .25),
        (cx + r * .05, cy - r * .2, cx + r * .7, cy + r * .5),
    ]
    for p in parts:
        d.ellipse(p, fill=outline)
    inset = w
    for p in parts:
        d.ellipse([p[0] + inset, p[1] + inset, p[2] - inset, p[3] - inset], fill=fill)
    d.rectangle([cx - r * .35, cy + r * .1, cx + r * .5, cy + r * .5 - inset], fill=fill)
    d.line([cx - r * .3, cy + r * .5 - w / 2, cx + r * .45, cy + r * .5 - w / 2], fill=outline, width=w)


def draw_icon(d, kind, cx, cy, r, night=False):
    w = max(2, int(r * .08))
    if kind == "sun":
        (draw_moon if night else draw_sun)(d, cx, cy, r)
    elif kind == "partly":
        if night:
            draw_moon(d, cx + r * .25, cy - r * .3, r * .7)
        else:
            draw_sun(d, cx + r * .25, cy - r * .3, r * .7)
        draw_cloud(d, cx - r * .1, cy + r * .1, r * .85)
    elif kind == "cloud":
        draw_cloud(d, cx, cy, r)
    elif kind == "fog":
        draw_cloud(d, cx, cy - r * .2, r * .8)
        for i in range(3):
            y = cy + r * .45 + i * r * .17
            d.line([cx - r * .6, y, cx + r * .6, y], fill=BLACK, width=w)
    elif kind in ("rain", "drizzle", "showers", "storm"):
        if kind == "showers":
            draw_sun(d, cx + r * .3, cy - r * .45, r * .55)
        draw_cloud(d, cx, cy - r * .25, r * .85)
        if kind == "storm":
            pts = [(cx + r * .05, cy + r * .25), (cx - r * .15, cy + r * .6), (cx + r * .05, cy + r * .6), (cx - r * .1, cy + r * .95)]
            d.line(pts, fill=BLACK, width=w + 1)
        else:
            n = 3 if kind != "drizzle" else 4
            for i in range(n):
                x = cx - r * .35 + i * r * .7 / (n - 1)
                L = r * (.15 if kind == "drizzle" else .3)
                d.line([x, cy + r * .4, x - r * .1, cy + r * .4 + L], fill=BLACK, width=w)
    elif kind == "snow":
        draw_cloud(d, cx, cy - r * .25, r * .85)
        for i in range(3):
            x, y, s = cx - r * .35 + i * r * .35, cy + r * .6, r * .12
            for a in (0, math.pi / 3, 2 * math.pi / 3):
                d.line([x - math.cos(a) * s, y - math.sin(a) * s, x + math.cos(a) * s, y + math.sin(a) * s], fill=BLACK, width=max(2, w - 1))


def text_c(d, xy, txt, f, fill=BLACK, anchor="mm"):
    d.text(xy, txt, font=f, fill=fill, anchor=anchor)


def render(now, wx):
    img = Image.new("L", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # --- Nagłówek: dzień tygodnia + data ---
    d.rectangle([0, 0, W, 120], fill=BLACK)
    text_c(d, (W / 2, 42), DAYS[now.weekday()].upper(), font(42, cond=True), WHITE)
    text_c(d, (W / 2, 92), f"{now.day} {MONTHS_GEN[now.month - 1]} {now.year}", font(30), WHITE)

    y0 = 128
    if wx is None:
        text_c(d, (W / 2, y0 + 120), "Brak danych pogodowych", font(28), GRAY)
    else:
        cur = wx["current"]
        desc, kind = describe(cur["weather_code"])
        night = cur.get("is_day", 1) == 0
        draw_icon(d, kind, 105, y0 + 85, 75, night)
        temp = round(cur["temperature_2m"])
        d.text((215, y0 + 2), f"{temp}°", font=font(96, bold=True), fill=BLACK)
        d.text((220, y0 + 118), desc, font=font(26, bold=True), fill=BLACK)
        daily = wx["daily"]
        hi, lo = round(daily["temperature_2m_max"][0]), round(daily["temperature_2m_min"][0])
        d.text((220, y0 + 152), f"max {hi}°  min {lo}°   odczuw. {round(cur['apparent_temperature'])}°",
               font=font(20), fill=BLACK)
        sr = daily["sunrise"][0][-5:]
        ss = daily["sunset"][0][-5:]
        d.text((220, y0 + 178), f"wiatr {round(cur['wind_speed_10m'])} km/h   wilg. {cur['relative_humidity_2m']}%",
               font=font(20), fill=BLACK)
        d.text((30, y0 + 178), f"↑{sr}  ↓{ss}", font=font(18), fill=GRAY)

        # --- Prognoza godzinowa ---
        y1 = y0 + 210
        d.line([20, y1, W - 20, y1], fill=LIGHT, width=2)
        times = wx["hourly"]["time"]
        start = next(i for i, t in enumerate(times) if dt.datetime.fromisoformat(t).replace(tzinfo=TZ) > now)
        cols = 6
        cw = (W - 40) / cols
        for k in range(cols):
            i = start + k * 2
            x = 20 + cw * k + cw / 2
            hh = times[i][11:13]
            text_c(d, (x, y1 + 18), f"{hh}:00", font(17), GRAY)
            _, kd = describe(wx["hourly"]["weather_code"][i])
            draw_icon(d, kd, x, y1 + 52, 22, wx["hourly"]["is_day"][i] == 0)
            text_c(d, (x, y1 + 90), f"{round(wx['hourly']['temperature_2m'][i])}°", font(24, bold=True))
            p = wx["hourly"]["precipitation_probability"][i]
            text_c(d, (x, y1 + 113), f"{p}%" if p is not None else "", font(15), GRAY)

        # --- Kolejne dni ---
        y2 = y1 + 128
        d.line([20, y2, W - 20, y2], fill=LIGHT, width=2)
        cw = (W - 40) / 4
        for k in range(1, 5):
            x = 20 + cw * (k - 1) + cw / 2
            day = dt.date.fromisoformat(daily["time"][k])
            text_c(d, (x, y2 + 17), DAYS_SHORT[day.weekday()] + f" {day.day}", font(19, bold=True))
            _, kd = describe(daily["weather_code"][k])
            draw_icon(d, kd, x - 35, y2 + 50, 20)
            text_c(d, (x + 25, y2 + 42), f"{round(daily['temperature_2m_max'][k])}°", font(22, bold=True))
            text_c(d, (x + 25, y2 + 64), f"{round(daily['temperature_2m_min'][k])}°", font(18), GRAY)

    # --- Kalendarz miesiąca ---
    yc = 572
    d.line([20, yc - 8, W - 20, yc - 8], fill=LIGHT, width=2)
    text_c(d, (W / 2, yc + 12), f"{MONTHS_NOM[now.month - 1]} {now.year}", font(22, bold=True))
    cal = calendar.Calendar(firstweekday=0).monthdayscalendar(now.year, now.month)
    cw = (W - 60) / 7
    gy = yc + 38
    for j, s in enumerate(DAYS_SHORT):
        text_c(d, (30 + cw * j + cw / 2, gy), s, font(17, bold=True), GRAY if j < 5 else BLACK)
    rh = min(30, (H - 26 - (gy + 14)) / len(cal))
    for r, week in enumerate(cal):
        for j, dd in enumerate(week):
            if not dd:
                continue
            x = 30 + cw * j + cw / 2
            y = gy + 14 + rh * r + rh / 2
            if dd == now.day:
                d.rounded_rectangle([x - 22, y - rh / 2 + 1, x + 22, y + rh / 2 - 1], radius=6, fill=BLACK)
                text_c(d, (x, y), str(dd), font(19, bold=True), WHITE)
            else:
                text_c(d, (x, y), str(dd), font(19, bold=j >= 5), BLACK if dd > now.day or j >= 5 else GRAY)

    # --- Stopka ---
    text_c(d, (W / 2, H - 12), f"{CITY} · aktualizacja {now:%H:%M}", font(14), GRAY)
    return img


def main():
    now = dt.datetime.now(TZ)
    try:
        wx = json.load(open(os.environ["WX_JSON"])) if os.environ.get("WX_JSON") else fetch_weather()
    except Exception as e:
        print("Pogoda niedostępna:", e, file=sys.stderr)
        wx = None
    if os.environ.get("FAKE_NOW"):
        now = dt.datetime.fromisoformat(os.environ["FAKE_NOW"]).replace(tzinfo=TZ)
    render(now, wx).save(OUT, optimize=True)
    print("Zapisano", OUT)


if __name__ == "__main__":
    main()
