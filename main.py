import json
import os
from dotenv import load_dotenv

import google.generativeai as genai
import google.generativeai.types as gap_types

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
schema_txt = """
{
  "operationType": "",
  "brand": "",
  "model": "",
  "year": 0,
  "color": "",
  "fuel_type": "",
  "transmission": "",
  "estado": "",
  "municipio": ""
}
"""

# 2. Crie a configuração de geração para forçar a saída JSON
generation_config = gap_types.GenerationConfig(
    response_mime_type="application/json",
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

    SCHEMA PERMITIDO:
    {schema_txt}

    Pedido do usuário:
    "{texto_usuario}"
    """
    
    try:
        # IMPORTANTE: Use .generate_content_async para não bloquear o servidor
        response = await model.generate_content_async(prompt)
        json_str = response.text.strip()
        start_index = json_str.find('{')
        end_index = json_str.rfind('}')
        # Se encontrou um JSON válido (com início e fim)
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = json_str[start_index:end_index+1]
        else:
            # Se não encontrou, a string é lixo, falha intencional
            print(f"Erro: Não foi possível extrair um objeto JSON da resposta: {json_str}")
            # Retorna vazio, pois o JSON.loads() falharia de qualquer forma
            return {}
        
        # O .strip() final é bom caso haja espaços em branco
        json_str = json_str.strip()

        if not json_str:
            print("Erro: A API retornou uma string vazia.")
            return {}
        
        filtro = json.loads(json_str)
        return filtro, None # Retorna (dados, erro)
    except json.JSONDecodeError:
        print(f"Erro: Falha ao decodificar o JSON. Resposta: {json_str}")
        return {}
    except Exception as e:
        # Captura outros erros (ex: API, validação, feedback do prompt)
        print(f"Erro inesperado na API: {e}")
        # Se a API recusar o prompt, 'response' pode não ter 'text'
        # e pode ter 'prompt_feedback' com o motivo.
        if 'response' in locals() and hasattr(response, 'text'):
             print(f"Resposta recebida: {response.text}")
        else:
             print("Resposta da API não foi recebida com sucesso.")
        return {}

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