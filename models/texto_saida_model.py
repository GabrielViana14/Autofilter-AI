from pydantic import BaseModel
from models.carro_model import CarroModel

class TextoSaidaModel(BaseModel):
    texto: str
    recomendacoes: list[CarroModel]