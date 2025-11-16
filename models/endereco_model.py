from pydantic import BaseModel
from typing import Optional
from models.local_model import LocalModel

class EnderecoModel(BaseModel):
    """
    Define a estrutura do endereço.
    O endereço completo e todos os seus campos são opcionais.
    """
    cep: Optional[str] = None
    rua: Optional[str] = None
    numero: Optional[str] = None
    logradouro: Optional[str] = None
    estado: Optional[str] = None
    municipio: Optional[str] = None
    location: Optional[LocalModel] = None   

