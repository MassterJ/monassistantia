import gradio as gr
import requests
import os

# --- CONFIGURATION AMÉLIORÉE ---
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

# 1. NOTRE LISTE DE MODÈLES DE SECOURS (du plus désiré au moins désiré)
# Nous allons essayer ces modèles dans l'ordre jusqu'à en trouver un qui fonctionne.
MODEL_ENDPOINTS = [
    "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill",
    "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
    # On pourrait en ajouter d'autres ici à l'avenir
]

# 2. Une variable pour stocker le modèle qui fonctionne actuellement
active_model_url = ""
active_model_name = "Indisponible"

# --------------------------------------------------------------------

def find_active_model():
    """
    NOUVELLE FONCTION : C'est le "vérificateur d'URL".
    Il parcourt notre liste et s'arrête au premier modèle qui répond correctement.
    Cette fonction est appelée une seule fois au démarrage de l'application.
    """
    global active_model_url, active_model_name
    
    print("--- Recherche d'un modèle d'IA actif ---")
    for url in MODEL_ENDPOINTS:
        model_name = url.split("/")[-1] # Extrait le nom du modèle de l'URL
        print(f"Test du modèle : {model_name}...")
        
        try:
            # On envoie une requête de test simple pour voir si le modèle est accessible
            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
                json={"inputs": "Hello"},
                timeout=15 # On n'attend pas plus de 15 secondes
            )
            # Si le serveur répond sans erreur (status 200), c'est notre champion !
            if response.status_code == 200:
                active_model_url = url
                active_model_name = model_name
                print(f"SUCCÈS ! Modèle actif : {active_model_name}")
                return # On a trouvé, on arrête la recherche
        except requests.exceptions.RequestException as e:
            # Si le modèle ne répond pas, on passe au suivant
            print(f"ÉCHEC du modèle {model_name}: {e}")
            continue
            
    if not active_model_url:
        print("AVERTISSEMENT : Aucun modèle d'IA n'a pu être contacté.")

def get_bot_response(message, history):
    """
    Cette fonction prend le message de l'utilisateur et renvoie la réponse de l'IA.
    Elle utilise maintenant le modèle que nous avons trouvé au démarrage.
    """
    # Si aucun modèle n'a été trouvé au démarrage, on renvoie une erreur.
    if not active_model_url:
        return "Désolé, tous les modèles d'IA sont actuellement indisponibles. Veuillez redémarrer l'application."

    payload = {"inputs": message}
    api_response = None
    try:
        # On utilise l'URL du modèle actif
        api_response = requests.post(active_model_url, headers={"Authorization": f"Bearer {HF_API_TOKEN}"}, json=payload)
        api_response.raise_for_status()
        output = api_response.json()
        
        bot_message = output[0].get("generated_text", "Désolé, je n'ai pas de réponse.")
        # On nettoie la réponse pour éviter qu'elle ne répète notre message
        if bot_message.strip().lower().startswith(message.strip().lower()):
             bot_message = bot_message[len(message):].lstrip()
        return bot_message

    except requests.exceptions.RequestException as e:
        print(f"--- ERREUR DE REQUÊTE API ---: {e}")
        if api_response is not None:
            print(f"Status Code: {api_response.status_code}, Réponse: {api_response.text}")
        return "Le modèle d'IA semble indisponible pour le moment, veuillez réessayer."

# --- Lancement de l'Application ---

# On lance la recherche du modèle actif AVANT de démarrer l'interface
find_active_model()

# On crée l'interface, en affichant le nom du modèle actif dans la description !
iface = gr.ChatInterface(
    fn=get_bot_response,
    title="Mon Assistant IA (Auto-Réparant)",
    description=f"Discutez avec un assistant intelligent. Modèle actuellement actif : {active_model_name}"
)

# Remplacez "iface.launch()" par cette ligne :
iface.launch(server_name="0.0.0.0", server_port=int(os.environ.get('PORT', 7860)))

