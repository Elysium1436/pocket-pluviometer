import datetime
from datetime import date
import ee
import asyncio


def ee_get_precipitation(date_before: str, date_after: str, lat: float, long: float):
    ponto = ee.Geometry.Point([long, lat])

    # GPM V7 dados de 30 minutos para um único dia
    dataset = (
        ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
        .filter(ee.Filter.date(date_before, date_after))
        .select("precipitation")
    )

    # Função para obter o valor de precipitação no ponto para cada imagem
    def get_precipitation_at_point(image: ee.image.Image):
        value = image.reduceRegion(
            reducer=ee.Reducer.first(), geometry=ponto, scale=1000
        ).get("precipitation")

        # Converte a precipitação de mm/h para mm em 30 minutos
        precipitation_30min = ee.Number(value).divide(2)

        return image.set(
            "stats",
            ee.Dictionary(
                {
                    "precipitation_30min": precipitation_30min,
                    "date": image.date().format("YYYY-MM-dd HH:mm:ss"),
                }
            ),
        )

    # Aplica a função a cada imagem na coleção
    values_at_point = dataset.map(get_precipitation_at_point).aggregate_array("stats")

    # Coleta os valores em uma lista para inspeção
    values_list = values_at_point.getInfo()

    # Dicionário para armazenar a precipitação acumulada por data
    daily_precipitation = {}

    # Calcula a precipitação acumulada diária
    for v in values_list:
        date_str = v["date"]
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
        precipitation = v["precipitation_30min"]

        daily_precipitation[date_obj] = (
            daily_precipitation.get(date_obj, 0) + precipitation
        )

    return [
        {"date": k, "daily_precipitation": v}
        for k, v in sorted(daily_precipitation.items(), key=lambda x: x[0])
    ]


async def get_data_google(
    lat: float,
    long: float,
    date_before: date,
    date_after: date,
):
    date_before = date_before.strftime("%Y-%m-%d")
    date_after = date_after.strftime("%Y-%m-%d")

    daily_precipitation = await asyncio.to_thread(
        ee_get_precipitation,
        date_before=date_before,
        date_after=date_after,
        lat=lat,
        long=long,
    )

    return daily_precipitation
