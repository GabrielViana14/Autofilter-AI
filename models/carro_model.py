from pydantic import BaseModel, Field
from typing import Optional
from models.endereco_model import EnderecoModel

class CarroModel(BaseModel):
    
    
    # --- Campos Obrigatórios (* Required) ---
    # O alias permite que o Python leia o campo "_id" do JSON
    id: str = Field(alias="_id")
    model: str
    brand: str
    year: int
    license_plate: str
    status: str # "available", "sold", etc.
    operationType: str # "sale" ou "rent"
    
    # Campos Opcionais (podem ser None ou não existir)
    operationType: Optional[str] = None
    price_per_hour: Optional[float] = None
    price: Optional[float] = None
    group: Optional[str] = None
    photo_url: Optional[str] = None
    status: Optional[str] = None
    rented_at: Optional[str] = None
    sold_at: Optional[str] = None
    rented_by: Optional[str] = None
    sold_to: Optional[str] = None
    short_description: Optional[str] = None
    mileage: Optional[float] = None
    address: Optional[EnderecoModel] = None # Modelo aninhado
    owner_id: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    
    class Config:
        populate_by_name = True # Permite que o Pydantic use o 'alias' "_id"