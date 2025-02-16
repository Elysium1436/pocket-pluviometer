from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from typing import Annotated
from .schemas.PluviometerInput import PluviometerInput
from .schemas.DailyPrecipitation import DailyPrecipitation
from .services.get_data_google import get_data_google
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import ee


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}

app = FastAPI()


def fake_hash_password(password: str):
    return "fakehashed" + password


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def fake_decode_token(token) -> User:
    return get_user(fake_users_db, token)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            401, "Invalid Auth Credentials", {"WWW-Authenticate": "Bearer"}
        )
    return user


async def get_current_active_user(user: Annotated[User, Depends(get_current_user)]):
    if user.disabled:
        raise HTTPException(400, "Inactive User")

    return user


# Check how to customize the request form


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(400, "Wrong username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(400, "Incorrect User or Password")

    return {"access_token": user.username, "token_type": "bearer"}


@app.on_event("startup")
async def gee_startup():
    # Caminho para o arquivo JSON de credenciais
    caminho_credenciais = "gee.json"
    # Inicializar a autenticação usando a função ServiceAccountCredentials
    credenciais = ee.ServiceAccountCredentials(
        "geeprojeto@ee-marcosadassan.iam.gserviceaccount.com", caminho_credenciais
    )
    ee.Initialize(credenciais)


@app.get("/users/me")
async def read_users_me(user: Annotated[User, Depends(get_current_active_user)]):
    return user


@app.get("/items")
def read_items(token: Annotated[dict, Depends(oauth2_scheme)]):
    return {"token": token}


@app.post("/pluviometer", response_model=list[DailyPrecipitation])
async def pluviometer(geographical_data: PluviometerInput) -> list[DailyPrecipitation]:
    lat = geographical_data.lat
    long = geographical_data.long
    date_before = geographical_data.date_before
    date_after = geographical_data.date_after

    precipitation_history = await get_data_google(lat, long, date_before, date_after)
    return precipitation_history
