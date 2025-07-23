import gradio as gr
import requests
import os
import json

# --- CONFIGURATION (Mise à jour pour Gemini 1.5 Pro) ---
API_KEY = os.getenv("GOOGLE_API_KEY")
# On change simplement "flash" en "pro" dans l'URL
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent?key={API_KEY}"
headers = {"Content-Type": "application/json"}
# ---------------------------------------------

# --- JavaScript pour la Synthèse Vocale ---
speak_js = """
// Fonction pour faire parler le navigateur
function speak_response(text) {
  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'fr-FR'; // On spécifie la langue française
    window.speechSynthesis.speak(utterance);
    return text; 
  } else {
    alert("Désolé, votre navigateur ne supporte pas la synthèse vocale.");
    return text;
  }
}
"""
# ---------------------------------------------

def get_bot_response(message, history):
    # La logique d'appel à l'API Gemini ne change pas
    formatted_history = []
    for user_msg, bot_msg in history:
        formatted_history.append({"role": "user", "parts": [{"text": user_msg}]})
        formatted_history.append({"role": "model", "parts": [{"text": bot_msg}]})

    formatted_history.append({"role": "user", "parts": [{"text": message}]})
    payload = {"contents": formatted_history}
    
    api_response = None
    try:
        api_response = requests.post(API_URL, headers=headers, json=payload, timeout=45) # Timeout augmenté pour le modèle Pro
        api_response.raise_for_status()
        output = api_response.json()
        bot_message = output["candidates"][0]["content"]["parts"][0]["text"]
        return bot_message
    except requests.exceptions.RequestException as e:
        print(f"--- ERREUR DE REQUÊTE API ---: {e}")
        return "Désolé, une erreur de communication est survenue avec l'API de Google."

# --- Interface avec gr.Blocks pour le contrôle vocal ---
with gr.Blocks(theme=gr.themes.Soft(), css="footer {display: none !important}") as iface:
    gr.Markdown(
        """
        # Mon Assistant IA Vocal
        Discutez avec l'assistant. Vous pouvez envoyer du texte ou des messages audio.
        """
    )
    
    chatbot = gr.Chatbot(height=500)
    msg = gr.Textbox(label="Votre message", placeholder="Écrivez votre message ici...")
    audio_mic = gr.Audio(sources=["microphone"], type="filepath", label="Ou enregistrez un message vocal")

    def respond(message, chat_history):
        bot_message = get_bot_response(message, chat_history)
        chat_history.append((message, bot_message))
        return "", chat_history, bot_message
    
    def transcribe_audio(audio_filepath, chat_history):
        if audio_filepath is None:
            return "", chat_history, None
        
        message = audio_filepath
        bot_message = get_bot_response(message, chat_history)
        chat_history.append((message, bot_message))
        return "", chat_history, bot_message

    msg.submit(respond, [msg, chatbot], [msg, chatbot, gr.Textbox(visible=False)], _js=speak_js)
    audio_mic.change(transcribe_audio, [audio_mic, chatbot], [msg, chatbot, gr.Textbox(visible=False)], _js=speak_js)

# --- Lancement de l'Interface ---
iface.launch(share=True)
