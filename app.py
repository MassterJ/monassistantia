import gradio as gr
import requests
import os
import json

# --- CONFIGURATION : GOOGLE GEMINI ---
API_KEY = os.getenv("GOOGLE_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"
headers = {"Content-Type": "application/json"}
# ---------------------------------------------

def get_bot_response(message, history):
    formatted_history = []
    for user_msg, bot_msg in history:
        formatted_history.append({"role": "user", "parts": [{"text": user_msg}]})
        formatted_history.append({"role": "model", "parts": [{"text": bot_msg}]})

    formatted_history.append({"role": "user", "parts": [{"text": message}]})
    payload = {"contents": formatted_history}
    
    api_response = None # <--- CORRECTION IMPORTANTE : On initialise la variable ici
    try:
        api_response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        api_response.raise_for_status()
        output = api_response.json()
        
        bot_message = output["candidates"][0]["content"]["parts"][0]["text"]
        return bot_message

    except requests.exceptions.RequestException as e:
        print(f"--- ERREUR DE REQUÊTE API ---: {e}")
        error_details = "Désolé, une erreur de communication est survenue avec l'API de Google."
        if api_response is not None:
             print(f"Réponse brute du serveur: {api_response.text}")
             try:
                 error_json = api_response.json()
                 error_details += f" (Détail: {error_json.get('error', {}).get('message', 'N/A')})"
             except json.JSONDecodeError:
                 pass
        return error_details

# --- Lancement de l'Interface ---
iface = gr.ChatInterface(
    fn=get_bot_response,
    title="Mon Assistant IA (Propulsé par Gemini)",
    description="Discutez avec un assistant basé sur le modèle Gemini 1.5 Flash de Google."
)

iface.launch(share=True)
