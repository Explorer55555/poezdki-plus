
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="MultiTravel Ultimate Engine v9.0")

MARKER = "766028"  # Твой маркер из Travelpayouts


def make_ostrovok_slug(city_name: str) -> str:
    translit_map = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "kh",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
        " ": "_",
        "-": "_",
    }
    clean_name = city_name.strip().lower()
    res = "".join(translit_map.get(c, c) for c in clean_name)
    res = res.strip("_")
    return f"russia/{res}"


# База IATA кодов и подсказок по погоде
CITY_INFO = {
    "сочи": {
        "iata": "AER",
        "weather": "🌤️ Средняя температура: +24°C, вода +23°C (Комфортный бархатный сезон)",
    },
    "адлер": {
        "iata": "AER",
        "weather": "🌤️ Средняя температура: +24°C, вода +23°C (Бархатный сезон)",
    },
    "дубай": {
        "iata": "DXB",
        "weather": "☀️ Солнечно, без осадков: +34°C, море +30°C (Идеально для пляжа)",
    },
    "стамбул": {
        "iata": "IST",
        "weather": "🌤️ Теплая прогулочная погода: +23°C (Отлично для экскурсий)",
    },
    "анталья": {
        "iata": "AYT",
        "weather": "☀️ Солнечно: +29°C, море +26°C (Пляжный сезон в разгаре)",
    },
    "санкт-петербург": {
        "iata": "LED",
        "weather": "Переменная облачность: +16°C (Рекомендуем взять легкую куртку)",
    },
    "питер": {
        "iata": "LED",
        "weather": "Переменная облачность: +16°C (Рекомендуем взять легкую куртку)",
    },
    "казань": {
        "iata": "KZN",
        "weather": "🌤️ Умеренно тепло: +18°C (Идеально для прогулок по Кремлю)",
    },
    "калининград": {
        "iata": "KGD",
        "weather": "🌤️ Балтийский бриз: +17°C (Комфортно для поездок к морю)",
    },
    "пхукет": {
        "iata": "HKT",
        "weather": "Тропическое тепло: +30°C, вода +28°C",
    },
    "ереван": {
        "iata": "EVN",
        "weather": "☀️ Ясно и тепло: +26°C",
    },
}

IATA_CODES = {
    "москва": "MOW",
    "екатеринбург": "SVX",
    "нижний новгород": "GOJ",
    "владивосток": "VVO",
    "новосибирск": "OVB",
    "красноярск": "KJA",
    "иркутск": "IKT",
    "уфа": "UFA",
    "самара": "KUF",
    "ростов-на-дону": "RVI",
    "краснодар": "KRR",
    "челябинск": "CEK",
    "тюмень": "TJM",
    "тбилиси": "TBS",
    "минск": "MSQ",
}


class MultiSearchQuery(BaseModel):
    from_city: str
    to_city: str
    date: str
    nights: int
    need_flight: bool = True
    need_train: bool = False
    need_hotel: bool = True
    need_car: bool = False


@app.get("/")
def read_root():
    return FileResponse("index.html")


@app.post("/api/v1/search")
def search_all(query: MultiSearchQuery):
    from_clean = query.from_city.strip().lower()
    to_clean = query.to_city.strip().lower()

    # Поиск IATA и Погоды
    dest_data = CITY_INFO.get(to_clean, {})
    origin_iata = (
        CITY_INFO.get(from_clean, {}).get("iata")
        or IATA_CODES.get(from_clean, "MOW")
    )
    dest_iata = dest_data.get("iata") or IATA_CODES.get(to_clean, "AER")

    weather_hint = dest_data.get(
        "weather", "🌤️ Комфортная погода для путешествий и отдыха"
    )

    ostrovok_path = make_ostrovok_slug(query.to_city)

    try:
        depart_date = datetime.strptime(query.date, "%Y-%m-%d")
        return_date = depart_date + timedelta(days=query.nights)

        depart_iso = depart_date.strftime("%Y-%m-%d")
        return_iso = return_date.strftime("%Y-%m-%d")

        depart_ru = depart_date.strftime("%d.%m.%Y")
        return_ru = return_date.strftime("%d.%m.%Y")

        depart_ddmm = depart_date.strftime("%d%m")
        return_ddmm = return_date.strftime("%d%m")

        ostrovok_dates_param = f"{depart_ru}-{return_ru}"
    except Exception:
        depart_iso = query.date
        return_iso = "2026-09-15"
        depart_ru = "10.09.2026"
        return_ru = "15.09.2026"
        ostrovok_dates_param = "10.09.2026-15.09.2026"
        depart_ddmm = "1009"
        return_ddmm = "1509"

    # Ссылки
    flight_buy_url = f"https://www.aviasales.ru/search/{origin_iata}{depart_ddmm}{dest_iata}{return_ddmm}1?marker={MARKER}"
    hotel_buy_url = f"https://ostrovok.ru/hotel/{ostrovok_path}/?dates={ostrovok_dates_param}&guests=1&marker={MARKER}"

    from_encoded = urllib.parse.quote(query.from_city)
    to_encoded = urllib.parse.quote(query.to_city)
    train_buy_url = f"https://travel.yandex.ru/trains/search/?fromName={from_encoded}&toName={to_encoded}&when={depart_iso}&marker={MARKER}"

    car_buy_url = f"https://localrent.com/?marker={MARKER}&city={query.to_city}&date_from={depart_iso}&date_to={return_iso}"

    return {
        "status": "success",
        "weather": weather_hint,
        "flights": [
            {
                "title": f"✈️ {query.from_city.capitalize()} ⇄ {query.to_city.capitalize()} (Билеты Эконом)",
                "details": f"Даты: {depart_iso} — {return_iso} ({query.nights} ночевки)",
                "url": flight_buy_url,
            }
        ]
        if query.need_flight
        else [],
        "hotels": [
            {
                "title": f"🏨 Отели в г. {query.to_city.capitalize()} (Ostrovok.ru)",
                "details": f"Даты: с {depart_ru} по {return_ru} ({query.nights} ночей)",
                "url": hotel_buy_url,
            }
        ]
        if query.need_hotel
        else [],
        "trains": [
            {
                "title": f"🚆 Поезда РЖД ({query.from_city.capitalize()} ➔ {query.to_city.capitalize()})",
                "details": f"Дата отправления: {depart_ru} (Яндекс.Путешествия)",
                "url": train_buy_url,
            }
        ]
        if query.need_train
        else [],
        "cars": [
            {
                "title": f"🚘 Прокат авто в г. {query.to_city.capitalize()}",
                "details": f"Период: {depart_iso} — {return_iso} ({query.nights} дней)",
                "url": car_buy_url,
            }
        ]
        if query.need_car
        else [],
    }
if __name__ == "__main__":

    import uvicorn



    uvicorn.run(app, host="0.0.0.0", port=80)









