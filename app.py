import gradio as gr
import requests
import os
import json

# --- CONFIGURATION ---
# Nous avons maintenant besoin des DEUX clés d'API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HF_API_TOKEN = os.getenv("HF_API_TOKEN") # Clé pour Hugging Face (Whisper)

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent?key={GOOGLE_API_KEY}"
WHISPER_API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"

gemini_headers = {"Content-Type": "application/json"}
whisper_headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
# ---------------------------------------------

def get_gemini_response(message, history):
    # La logique d'appel à Gemini ne change pas
    formatted_history = []
    for user_msg, bot_msg in history:
        if user_msg: formatted_history.append({"role": "user", "parts": [{"text": user_msg}]})
        if bot_msg: formatted_history.append({"role": "model", "parts": [{"text": bot_msg}]})
    formatted_history.append({"role": "user", "parts": [{"text": message}]})
    payload = {"contents": formatted_history}
    
    try:
        api_response = requests.post(GEMINI_API_URL, headers=gemini_headers, json=payload, timeout=45)
        api_response.raise_for_status()
        output = api_response.json()
        bot_message = output["candidates"][0]["content"]["parts"][0]["text"]
        return bot_message
    except requests.exceptions.RequestException as e:
        print(f"--- ERREUR API GEMINI ---: {e}")
        return "Désolé, une erreur de communication est survenue avec l'API de Google."

# --- NOUVELLE INTERFACE AVEC TRANSCRIPTION ---
with gr.Blocks(theme=gr.themes.Soft(), css="footer {display: none !important}") as iface:
    gr.Markdown("# Mon Assistant IA Vocal\nDiscutez avec l'assistant. Vous pouvez envoyer du texte ou des messages audio.")
    
    chatbot = gr.Chatbot(height=500)
    msg = gr.Textbox(label="Votre message", placeholder="Écrivez votre message ici...")
    audio_mic = gr.Audio(sources=["microphone"], type="filepath", label="Ou enregistrez un message vocal")

    def respond_text(message, chat_history):
        bot_message = get_gemini_response(message, chat_history)
        chat_history.append((message, bot_message))
        return "", chat_history

    def respond_audio(audio_filepath, chat_history):
        if audio_filepath is None:
            return "", chat_history
        
        # Étape 1: Envoyer l'audio à Whisper pour transcription
        print(f"Transcription du fichier audio : {audio_filepath}")
        try:
            with open(audio_filepath, "rb") as f:
                audio_data = f.read()
            api_response = requests.post(WHISPER_API_URL, headers=whisper_headers, data=audio_data, timeout=45)
            api_response.raise_for_status()
            transcribed_text = api_response.json()["text"]
            print(f"Texte transcrit : '{transcribed_text}'")
        except requests.exceptions.RequestException as e:
            print(f"--- ERREUR API WHISPER ---: {e}")
            return "", chat_history + [(f"(Erreur de transcription du fichier audio)", None)]

        # Étape 2: Envoyer le texte transcrit à Gemini
        bot_message = get_gemini_response(transcribed_text, chat_history)
        chat_history.append((transcribed_text, bot_message))
        return "", chat_history

    msg.submit(respond_text, [msg, chatbot], [msg, chatbot])
    audio_mic.change(respond_audio, [audio_mic, chatbot], [msg, chatbot])

iface.launch(share=True)
