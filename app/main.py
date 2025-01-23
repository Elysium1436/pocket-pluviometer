from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()


@app.route("/", methods=["GET"], response_class=PlainTextResponse)
def hello_world(request):
    return "Hello World"



