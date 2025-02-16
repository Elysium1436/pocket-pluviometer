from pydantic import BaseModel
from datetime import date


class PluviometerInput(BaseModel):
    lat: float
    long: float
    date_before: date
    date_after: date
