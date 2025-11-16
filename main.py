import json
import os
from dotenv import load_dotenv

import google.generativeai as genai
import google.generativeai.types as gap_types
from google.generativeai.types import Schema, Type

from fastapi import FastAPI, Depends, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.carro_model import CarroModel
from models.texto_entrada_model import TextoEntradaModel
from models.texto_saida_model import TextoSaidaModel
from typing import List, Dict, Any, Optional
import httpx

# --- Configuração Inicial ---
load_dotenv()

# Cria a instância da sua aplicação
app = FastAPI()

# Isso diz ao FastAPI que ele deve procurar por um header "Authorization: Bearer <token>"
security_scheme = HTTPBearer()

# --- Configuração do Gemini ---
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Erro Crítico: GEMINI_API_KEY não foi definida.")
else:
    genai.configure(api_key=api_key)

# 1. Defina o SCHEMA do Gemini
schema_definition = Schema(
    type=Type.OBJECT,
    properties={
        'operationType': Schema(type=Type.STRING),
        'price_min': Schema(type=Type.NUMBER),
        'price_max': Schema(type=Type.NUMBER),
        'brand': Schema(type=Type.STRING),
        'model': Schema(type=Type.STRING),
        'year': Schema(type=Type.NUMBER),
        'color': Schema(type=Type.STRING),
        'fuel_type': Schema(type=Type.STRING),
        'transmission': Schema(type=Type.STRING),
        'mileage_max': Schema(type=Type.NUMBER),
        'estado': Schema(type=Type.STRING),
        'municipio': Schema(type=Type.STRING),
    }
)

# 2. Crie a configuração de geração para forçar a saída JSON
generation_config = gap_types.GenerationConfig(
    response_mime_type="application/json",
    response_schema=schema_definition
)

# 3. Inicialize o modelo
model = genai.GenerativeModel("models/gemini-2.5-flash")

async def gerar_filtro_gemini_async(texto_usuario: str):
    """
    Função ASSÍNCRONA que chama a API do Gemini.
    """
    prompt = f"""
    Você é um assistente de e-commerce especializado em extrair
    filtros de uma linguagem natural.

    Seu objetivo é ler o pedido do usuário e extrair as entidades
    relevantes para preencher os campos do filtro JSON.

    REGRAS DE EXTRAÇÃO:
    1. Para pedidos de preço:
       - “abaixo de X”, “menos de X”, “até X” → "price_max": X
       - “acima de X”, “mais de X”, “a partir de X” → "price_min": X
    2. Para pedidos de quilometragem:
       - “menos de X km”, “até X km” → "mileage_max": X
    3. Mapeie os valores de transmissão: "automático" -> "automático", "manual" -> "manual".
    4. Se um valor não for mencionado no pedido, omita-o do JSON.

    Pedido do usuário:
    "{texto_usuario}"
    """
    
    try:
        # IMPORTANTE: Use .generate_content_async para não bloquear o servidor
        response = await model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        json_str = response.text.strip()
        filtro = json.loads(json_str)
        return filtro, None # Retorna (dados, erro)
    except Exception as e:
        print(f"Erro ao chamar a API Gemini: {e}")
        return None, str(e)

# --- Rotas da Aplicação ---

# Rota para a raiz do site
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# Sua rota original (sem modificações)
@app.get("/get_all_cars", response_model=list[CarroModel])
async def get_all_cars( token: HTTPAuthorizationCredentials = Security(security_scheme) ):
    url_carro = 'https://navy-backend.onrender.com/api/cars'
    headers = {
        "Authorization": f"Bearer {token.credentials}"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url_carro, headers=headers)
            
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Token inválido ou expirado na API externa")
            
            response.raise_for_status() 
            dados = response.json()
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, 
                detail=f"Erro da API externa: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return dados

@app.post("/generate_filter", response_model=Dict[str, Any])
async def handle_filter_request(
    # Usa seu Pydantic model para pegar o texto de entrada
    entrada: TextoEntradaModel, 
    # Protege a rota com o mesmo esquema de segurança
    token: HTTPAuthorizationCredentials = Security(security_scheme) 
):
    """
    Esta é a rota da API que seu frontend irá chamar.
    Espera um JSON no corpo da requisição com a chave "text".
    Ex: { "text": "carro vermelho automático" }
    """
    if not entrada.text:
        raise HTTPException(status_code=400, detail="O campo 'text' não pode ser vazio.")

    # Chama nossa função async do Gemini
    filtro, erro = await gerar_filtro_gemini_async(entrada.text)
    
    if erro:
        # Se a API do Gemini falhar, retorne um erro 500
        raise HTTPException(status_code=500, detail=f"Erro ao processar o pedido: {erro}")
    
    # Sucesso! Retorna o filtro JSON
    return filtro