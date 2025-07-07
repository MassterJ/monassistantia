import gradio as gr
import requests
import os

# --- CONFIGURATION ---
# Récupère la clé API depuis les "Secrets" de la plateforme d'hébergement.
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

# Liste des modèles à essayer, par ordre de préférence.
MODEL_ENDPOINTS = [
    "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
    "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill",
]

# Variable globale pour stocker l'URL du modèle qui fonctionne.
active_model_url = None
# --------------------

def find_and_set_active_model():
    """
    Cherche un modèle actif dans la liste et met à jour la variable globale.
    N'est appelée que si aucun modèle n'est déjà actif.
    """
    global active_model_url
    print("--- Aucun modèle actif. Lancement de la recherche... ---")
    
    for url in MODEL_ENDPOINTS:
        model_name = url.split("/")[-1]
        print(f"Test du modèle : {model_name}...")
        try:
            # On envoie une requête de test avec un timeout généreux.
            response = requests.post(url, headers=headers, json={"inputs": "test"}, timeout=45)
            if response.status_code == 200:
                print(f"SUCCÈS ! Modèle actif trouvé : {model_name}")
                active_model_url = url
                return True  # Succès, on arrête la recherche.
        except requests.exceptions.RequestException:
            print(f"ÉCHEC du modèle {model_name}. Essai du suivant.")
            continue
            
    print("AVERTISSEMENT : Aucun modèle d'IA n'a pu être contacté.")
    return False  # Échec, aucun modèle n'a été trouvé.

def get_bot_response(message, history):
    """
    Fonction principale appelée par l'interface de chat.
    """
    global active_model_url
    
    # Si aucun modèle n'est mémorisé, on en cherche un maintenant.
    if not active_model_url:
        if not find_and_set_active_model():
            return "Désolé, tous les modèles d'IA sont injoignables pour le moment. Veuillez redémarrer l'application."

    # On utilise le modèle actif pour la conversation.
    payload = {"inputs": message}
    try:
        api_response = requests.post(active_model_url, headers=headers, json=payload)
        api_response.raise_for_status() # Lève une erreur en cas de 4xx ou 5xx
        output = api_response.json()
        
        # On nettoie la réponse qui répète souvent la question de l'utilisateur.
        generated_text = output[0].get("generated_text", "Désolé, je n'ai pas de réponse.")
        if generated_text.strip().lower().startswith(message.strip().lower()):
             bot_message = generated_text[len(message):].strip()
        else:
             bot_message = generated_text.strip()
        return bot_message
        
    except requests.exceptions.RequestException as e:
        print(f"Erreur durant la conversation : {e}")
        # On réinitialise le modèle actif en cas d'erreur pour forcer une nouvelle recherche.
        active_model_url = None
        return "Une erreur de communication est survenue. Veuillez renvoyer votre message."

# --- Lancement de l'Interface ---
iface = gr.ChatInterface(
    fn=get_bot_response,
    title="Mon Assistant IA (Robuste)",
    description="Discutez avec un assistant intelligent. Le premier message peut être lent car il initialise la connexion."
)

# Configuration du lancement pour être compatible avec les plateformes de déploiement comme Render.
iface.launch(server_name="0.0.0.0", server_port=int(os.environ.get('PORT', 7860)))


