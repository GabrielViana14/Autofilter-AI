# Autofilter AI

## **Visão Geral**:
- **Descrição**: Projeto FastAPI que expõe endpoints para gerar e aplicar filtros de busca de carros a partir de texto livre. Usa o serviço em `services/filter_service.py` para extrair filtros JSON (via API generativa) e consulta uma API externa de carros em `main.py`.
- **Endpoint principais**: `GET /` (saudação) e `GET /get_all_cars` (retorna lista de carros — requer `Authorization: Bearer <token>`).

## **Pré-requisitos**:
- **Python**: `Python 3.10+` recomendado.
- **Variáveis de ambiente**: crie um arquivo `.env` com `GEMINI_API_KEY=<sua_chave>` (usado por `services/filter_service.py`).
- **Dependências**: o arquivo `requirements.txt` presente contém atualmente apenas `pillow==11.3.0`. Instale também manualmente (se necessário) `fastapi`, `httpx`, `uvicorn`, `pydantic`, `python-dotenv` e o cliente da API generativa que você usa.

## **Instalação (PowerShell)**:
1. Crie e ative um virtualenv
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```

2. Atualize pip e instale dependências listadas
    ```powershell
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    ```

3. Instale pacotes adicionais necessários (caso não estejam no requirements)
    ```powershell
    python -m pip install fastapi httpx uvicorn pydantic python-dotenv pillow
    ```
4. Se você usa o SDK do Google Gemini/Generative AI, instale o pacote correspondente.  
Exemplo (pode variar):
    ```powershell
    python -m pip install google-generative-ai
    ```

> Observação: ajuste o nome do pacote do SDK generativo conforme o provedor (o import no código é `google.generativeai`).

## **Configuração**:
- Crie um arquivo `.env` com a chave da API generativa:
```
GEMINI_API_KEY=your_api_key_here
```
- O serviço `main.py` também consome uma API externa de carros. Para usar `/get_all_cars` é preciso fornecer um token válido via header `Authorization: Bearer <token>`.

**Executando a aplicação**:
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- Acesse `http://127.0.0.1:8000/` para verificar a rota raiz.

**Exemplo de chamada para `/get_all_cars` (curl)**:
```bash
curl -H "Authorization: Bearer <seu_token_aqui>" http://127.0.0.1:8000/get_all_cars
```

**Exemplo em PowerShell (Invoke-RestMethod)**:
```powershell
$headers = @{ Authorization = 'Bearer <seu_token_aqui>' }
Invoke-RestMethod -Uri http://127.0.0.1:8000/get_all_cars -Headers $headers -Method Get
```

## **Estrutura do projeto**:
- `main.py` — Aplicação FastAPI e endpoints.
- `services/filter_service.py` — Lógica que chama a API generativa (Gemini/Generative AI) para extrair filtros JSON do texto do usuário. Requer `GEMINI_API_KEY` no `.env`.
- `models/` — Models Pydantic usados nas respostas e requisições (ex.: `carro_model.py`, `texto_entrada_model.py`, `texto_saida_model.py`, etc.).
- `requirements.txt` — Lista de dependências do projeto (atualmente só contém `pillow==11.3.0`).

### **Modelos (resumo)**:
- `models/carro_model.py` — representa um carro (usado como `response_model` em `get_all_cars`).
- `models/texto_entrada_model.py` e `models/texto_saida_model.py` — usados para entrada/saída de texto e geração de filtros.

### **Serviços**:
- `services/filter_service.py` monta um prompt e chama o modelo generativo para retornar um JSON com campos de filtro (ex.: `brand`, `model`, `year`, `price_min`, `price_max`, etc.). O arquivo valida e limpa a resposta JSON antes de retornar um dicionário Python.

### **Boas práticas / observações**:
- Garanta que o interpretador Python do VS Code seja o mesmo onde você instalou as dependências (escolha o interpreter no canto inferior direito do VS Code e, se necessário, reinicie o Language Server).
- Atualize `requirements.txt` depois de instalar pacotes com:
```powershell
python -m pip freeze > requirements.txt
```
- Proteja chaves e tokens: não commit `GEMINI_API_KEY` nem tokens em repositórios públicos.

