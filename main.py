from fastapi import FastAPI
from pydantic import BaseModel
from scraper import rodar_robo_sigaa

app = FastAPI()

class LoginSigaa(BaseModel):
    usuario: str
    senha: str

@app.get("/")
def home():
    return {"status": "Robô online 🤖"}

@app.post("/sincronizar")
def sincronizar(dados: LoginSigaa):
    resultado = rodar_robo_sigaa(dados.usuario, dados.senha)
    return resultado