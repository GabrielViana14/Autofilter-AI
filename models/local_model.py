from pydantic import BaseModel
from typing import Optional

class LocalModel(BaseModel):
    """
    Define a estrutura de geolocalização.
    Todos os campos são opcionais.
    """
    latitude: Optional[float] = None
    longitude: Optional[float] = None