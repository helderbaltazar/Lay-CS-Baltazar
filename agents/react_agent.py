"""
agents/react_agent.py

Motor ReAct (Reason + Act) usando Gemini 1.5 Pro para SRE.
Analisa erros dinamicamente e decide qual ferramenta de remediação chamar.
"""
import os
import json
import google.generativeai as genai
from agents.tools import (
    trigger_fallback_mode,
    refresh_layback_cookies,
    send_telegram_alert
)

# Ferramentas disponíveis para o agente SRE
AVAILABLE_TOOLS = {
    "trigger_fallback_mode": trigger_fallback_mode,
    "refresh_layback_cookies": refresh_layback_cookies,
    "send_telegram_alert": send_telegram_alert
}

def init_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY não configurada.")
    genai.configure(api_key=api_key)
    # Usando 1.5 Pro para SRE conforme regra do AGENTS.md
    return genai.GenerativeModel("gemini-1.5-pro-latest")

def diagnose_and_heal(step: str, error_msg: str, traceback_str: str) -> bool:
    """
    Envia o erro para o Gemini 1.5 Pro. O modelo decide qual ferramenta usar.
    Retorna True se aplicou uma remediação e o fluxo deve tentar de novo.
    Retorna False se decidiu que não há como recuperar agora.
    """
    try:
        model = init_gemini()
    except Exception as e:
        print(f"[SRE Agent] ⚠️ Não foi possível iniciar o Gemini: {e}")
        return False
        
    prompt = f"""
Você é um Agente SRE (Site Reliability Engineer) autônomo.
Sua missão é recuperar a pipeline de injeção que acabou de falhar no passo '{step}'.

Erro capturado:
{error_msg}

Traceback:
{traceback_str}

Suas ferramentas de remediação disponíveis:
1. refresh_layback_cookies(): Use se o erro for de autenticação (401, Invalid Cookie, Unauthorized).
2. trigger_fallback_mode(): Use se a API do TheOdds/DataFootball estiver caindo (500, timeout constante) ou se esgotar quota 429 da própria IA. Ativa o modo puramente estatístico.
3. send_telegram_alert(message, level): Envia alerta customizado. Use 'level="critical"' para falhas graves.

Responda EXCLUSIVAMENTE com um JSON no formato:
{{
  "thought": "seu raciocínio passo a passo sobre o que causou o erro",
  "tool_to_call": "nome_da_ferramenta" (ou null se impossível recuperar),
  "tool_args": {{ "message": "...", "level": "..." }} (apenas para telegram_alert, vazio nas outras),
  "should_retry": true (se a ferramenta aplicada tem chance de consertar o erro) ou false
}}
"""
    print(f"[SRE Agent] 🧠 Consultando Gemini 1.5 Pro para auto-healing do passo '{step}'...")
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        decision = json.loads(response.text)
        
        print(f"[SRE Agent] 💭 Raciocínio: {decision.get('thought')}")
        tool_name = decision.get('tool_to_call')
        
        if tool_name and tool_name in AVAILABLE_TOOLS:
            print(f"[SRE Agent] 🔧 Invocando ferramenta: {tool_name}()")
            tool_func = AVAILABLE_TOOLS[tool_name]
            args = decision.get('tool_args', {})
            
            # Executa a ferramenta
            if args:
                tool_func(**args)
            else:
                tool_func()
                
            return decision.get('should_retry', False)
        else:
            print("[SRE Agent] ❌ Nenhuma ferramenta aplicável escolhida.")
            return False
            
    except Exception as e:
        print(f"[SRE Agent] 💥 Falha catastrófica no cérebro SRE: {e}")
        return False
