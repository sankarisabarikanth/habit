import requests

def get_ai_coach_response(user_message, chat_history=None):
    """
    Generates a response from the google/gemma-3n-e2b-it model acting as Aura Coach.
    """
    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    
    headers = {
        "Authorization": "Bearer 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",
        "Accept": "application/json"
    }
    
    system_prompt = (
        "You are Aura Coach, a premium productivity and habit advisor. "
        "Provide brief, motivational, and extremely practical advice on "
        "habit formation, consistency, discipline, and routines. "
        "Keep your output readable, encouraging, and clear. "
        "Address the user as a fellow builder of routines."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Append history if present
    if chat_history:
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
    messages.append({"role": "user", "content": user_message})
    
    payload = {
        "model": "google/gemma-3n-e2b-it",
        "messages": messages,
        "max_tokens": 512,
        "temperature": 0.20,
        "top_p": 0.70,
        "frequency_penalty": 0.00,
        "presence_penalty": 0.00,
        "stream": False
    }
    
    try:
        response = requests.post(invoke_url, headers=headers, json=payload)
        response.raise_for_status()
        
        res_json = response.json()
        choice = res_json["choices"][0]["message"]
        content = choice.get("content", "")
        reasoning = choice.get("reasoning_content", None)
        
        return {
            "status": "success",
            "content": content,
            "reasoning": reasoning
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
