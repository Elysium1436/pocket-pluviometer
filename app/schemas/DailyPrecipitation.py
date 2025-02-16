from pydantic import BaseModel
import datetime


class DailyPrecipitation(BaseModel):
    date: datetime.date
    daily_precipitation: float
