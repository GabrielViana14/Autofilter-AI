from fastapi import  FastAPI, Depends, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
from models.carro_model import CarroModel
from models.texto_entrada_model import TextoEntradaModel
from models.texto_saida_model import TextoSaidaModel
from typing import List, Dict, Any, Optional
import httpx
import re

# Cria a instância da sua aplicação
app = FastAPI()

# Isso diz ao FastAPI que ele deve procurar por um header "Authorization: Bearer <token>"
security_scheme = HTTPBearer()

# Rota para a raiz do site
@app.get("/")
def read_root():
    return {"message": "Hello, World!"} 

@app.get("/get_all_cars", response_model=list[CarroModel])
async def get_all_cars( token: HTTPAuthorizationCredentials = Security(security_scheme) ):
    url_carro = 'https://navy-backend.onrender.com/api/cars'  # Substitua pela URL real da API de carros

    headers = {
        "Authorization": f"Bearer {token.credentials}"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url_carro, headers=headers)

            # 4. (BOA PRÁTICA) Verificar se a API externa aceitou o token
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Token inválido ou expirado na API externa")
            
            # Gerar erro para outras respostas ruins (ex: 500)
            response.raise_for_status() 
            
            dados = response.json()
            
        except httpx.HTTPStatusError as e:
            # Se a API externa falhar (ex: 500, 404), seu app vai reportar
            raise HTTPException(
                status_code=e.response.status_code, 
                detail=f"Erro da API externa: {e.response.text}"
            )
        except Exception as e:
            # Pega outros erros (ex: rede, timeout)
            raise HTTPException(status_code=500, detail=str(e))
    
    # Se tudo deu certo, o Pydantic valida e retorna os dados
    return dados

