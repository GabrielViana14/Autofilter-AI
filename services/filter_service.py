import json
import google.generativeai as genai
import google.generativeai.types as gap_types
from dotenv import load_dotenv
import os

load_dotenv()  # carrega as variáveis do .env

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Erro: GEMINI_API_KEY não encontrada no .env")
    exit()

genai.configure(api_key=api_key)


# Isto é o que define a *estrutura* da saída JSON esperada.
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

def gerar_filtro_carro_gemini(texto_usuario: str):
    """
    Recebe um texto do usuário e retorna o filtro JSON do carro
    conforme o schema definido.
    """

    prompt = f"""
    Você é um assistente de e-commerce especializado em extrair
    filtros de uma linguagem natural.

    Seu objetivo é ler o pedido do usuário e extrair as entidades
    relevantes para preencher os campos do filtro JSON.

    REGRAS DE EXTRAÇÃO:
    1. Para pedidos de preço:
       - “abaixo de X”, “menos de X”, “até X”, “mais barato que X”
         → usar "price_max": X
       - “acima de X”, “mais de X”, “a partir de X”, “mais caro que X”
         → usar "price_min": X
    2. Para pedidos relacionados à quilometragem:
       - “menos de X km”, “até X km”, “abaixo de X km”
         → usar "mileage_max": X
    3. Mapeie os valores de transmissão: "automático" -> "automático", "manual" -> "manual".
    4. Se um valor não for mencionado no pedido, omita-o do JSON.

    SCHEMA PERMITIDO:
    {schema_txt}

    Pedido do usuário:
    "{texto_usuario}"
    """

    model = genai.GenerativeModel("models/gemini-2.5-flash") # Modelo para retorno rapido

    try:
        # 4. Passe o generation_config para o modelo
        response = model.generate_content(prompt)

        # 5. Corrija a extração do texto da resposta.
        # O atalho 'response.text' é a forma mais fácil e segura.
        # O JSON Mode GARANTE que response.text será uma string JSON válida.
        json_str = response.text.strip()

        # Limpeza robusta, caso o modelo ainda envie os blocos de markdown
        # O modelo está retornando ```json\n{...}\n```
        # Vamos extrair o JSON encontrando o primeiro { e o último }
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

        # Tenta converter para dict
        filtro = json.loads(json_str)
        return filtro

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
