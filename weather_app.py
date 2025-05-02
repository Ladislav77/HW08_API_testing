import streamlit as st
import requests
import datetime
import sqlite3
import pandas as pd

api_key = st.secrets["OPENWEATHERMAP_API_KEY"]

DATABASE_NAME = "weather_history.db"
WEATHER_TABLE_NAME = "weather_data"

def create_weather_table():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {WEATHER_TABLE_NAME} (
            city TEXT,
            temperature REAL,
            humidity INTEGER,
            wind_speed REAL,
            timestamp DATETIME
        )
    """)
    conn.commit()
    conn.close()

create_weather_table()

def log_weather_data(city, temperature, humidity, wind_speed):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    now = datetime.datetime.now()
    cursor.execute(f"""
        INSERT INTO {WEATHER_TABLE_NAME} (city, temperature, humidity, wind_speed, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (city, temperature, humidity, wind_speed, now))
    conn.commit()
    conn.close()

@st.cache_data(ttl=600)
def get_current_weather_data(city):
    
    base_url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&lang=hu&units=metric'
    params = {
        "q": city,
        "appid": api_key    
    }
    response = requests.get(base_url, params=params)
    try:
        response.raise_for_status()  
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        st.warning("Hiba történt az időjárás adatainak lekérésekor")
        return None

st.title("RobotDreams Python időjárás app")  # Alkalmazás címe

city = st.text_input("Add meg a város nevét:", "Kolárovo")  # Szövegbeviteli mező a városnak

if city:  # Ha a felhasználó megadott egy városnevet
    weather_data = get_current_weather_data(city)  # Lekérjük az adatokat

    if weather_data:  # Ha sikerült lekérni az adatokat
        col1, col2, col3 = st.columns(3)  # Három oszlopot hozunk létre
        col1.metric("Hőmérséklet", f"{weather_data['main']['temp']:.1f} °C")  # Hőmérséklet
        col2.metric("Páratartalom", f"{weather_data['main']['humidity']}%")  # Páratartalom
        col3.metric("Szélsebesség", f"{weather_data['wind']['speed']:.1f} m/s")  # Szélsebesség

        st.subheader(f"{city} a térképen:")
        try:
            st.map({
                'latitude': [weather_data['coord']['lat']],
                'longitude': [weather_data['coord']['lon']]
            }, zoom=8)
        except KeyError:
            st.warning("A város koordinátái nem találhatóak.")

        log_weather_data(
            city=city,
            temperature=weather_data['main']['temp'],
            humidity=weather_data['main']['humidity'],
            wind_speed=weather_data['wind']['speed']
        )
    else:
        st.warning("Kérlek, adj meg egy létező városnevet.")

    if st.checkbox("Keresési előzmények megtekintése"):
        conn = sqlite3.connect(DATABASE_NAME)
        query = f"SELECT * FROM {WEATHER_TABLE_NAME} ORDER BY timestamp DESC"
        df = pd.read_sql_query(query, conn)
        st.dataframe(df)
        conn.close()
