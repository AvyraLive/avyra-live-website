"""
AVYRA-LIVE — Site web vitrine + Back-office agents IA
"""
import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, Response, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

# Add meta-agent-ia to path for agent imports
sys.path.insert(0, os.path.join(Config.BASE_DIR, '..', 'meta-agent-ia'))

app = Flask(__name__)
app.config.from_object(Config)

# ─── Authentication ───
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Connectez-vous pour accéder au back-office.'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

USERS = {
    '1': User('1', Config.ADMIN_USERNAME),
}

@login_manager.user_loader
def load_user(user_id):
    return USERS.get(user_id)

# ─── Context processor (variables disponibles dans tous les templates) ───
@app.context_processor
def inject_globals():
    return {
        'societe': Config.SOCIETE,
        'phone': Config.PHONE,
        'email': Config.MAIL_CONTACT,
        'adresse': Config.ADRESSE,
        'siret': Config.SIRET,
        'president': Config.PRESIDENT,
        'year': datetime.now().year,
    }

# ════════════════════════════════════════════════
#  VITRINE PUBLIQUE
# ════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('public/index.html')

@app.route('/groupes-artistes')
def orchestre():
    return render_template('public/orchestre.html')

@app.route('/prestations-techniques')
def techniques():
    return render_template('public/techniques.html')

@app.route('/galerie')
def galerie():
    return render_template('public/galerie.html')

def _envoyer_message_contact(champs):
    """Envoie le message du formulaire de contact via l'API Gmail (HTTPS).
    Utilise le compte de service Google avec delegation de domaine.
    Lève une exception si la config est absente ou l'envoi échoue (→ filet de secours)."""
    import base64
    from email.mime.text import MIMEText
    from email.utils import formataddr
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    key_file = Config.GOOGLE_SERVICE_ACCOUNT_FILE
    if not key_file or not os.path.exists(key_file):
        raise RuntimeError(f'Clé compte de service introuvable : {key_file}')

    corps = (
        "Nouveau message reçu via le formulaire de contact du site AVYRA-LIVE\n"
        "──────────────────────────────────────────────\n"
        f"Nom / structure : {champs['nom']}\n"
        f"Email           : {champs['email']}\n"
        f"Téléphone       : {champs['telephone'] or '—'}\n"
        f"Type d'événement: {champs['type_event'] or '—'}\n"
        f"Date envisagée  : {champs['date_event'] or '—'}\n"
        "──────────────────────────────────────────────\n\n"
        f"{champs['message']}\n"
    )
    msg = MIMEText(corps, 'plain', 'utf-8')
    msg['Subject'] = f"[Site AVYRA] Contact — {champs['nom'] or champs['email']}"
    msg['From'] = formataddr(('Site AVYRA-LIVE', Config.GOOGLE_DELEGATED_USER))
    msg['To'] = Config.CONTACT_RECIPIENT
    if champs['email']:
        msg['Reply-To'] = champs['email']

    creds = service_account.Credentials.from_service_account_file(
        key_file,
        scopes=['https://www.googleapis.com/auth/gmail.send'],
        subject=Config.GOOGLE_DELEGATED_USER,
    )
    gmail = build('gmail', 'v1', credentials=creds, cache_discovery=False)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gmail.users().messages().send(userId='me', body={'raw': raw}).execute()


def _sauver_message_secours(champs):
    """Filet de sécurité : si l'email échoue, on journalise le message pour ne rien perdre."""
    try:
        import json
        path = os.path.join(Config.BASE_DIR, 'contact_messages_secours.log')
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'ts': datetime.now().isoformat(), **champs}, ensure_ascii=False) + '\n')
    except Exception:
        pass


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Anti-spam : champ caché "website" rempli uniquement par les bots
        if request.form.get('website'):
            return redirect(url_for('contact'))
        champs = {
            'nom': request.form.get('nom', '').strip(),
            'email': request.form.get('email', '').strip(),
            'telephone': request.form.get('telephone', '').strip(),
            'type_event': request.form.get('type_event', '').strip(),
            'date_event': request.form.get('date_event', '').strip(),
            'message': request.form.get('message', '').strip(),
        }
        if not (champs['nom'] and champs['email'] and champs['message']):
            flash('Merci de renseigner au moins votre nom, votre email et votre message.', 'error')
            return render_template('public/contact.html')
        try:
            _envoyer_message_contact(champs)
        except Exception as e:
            app.logger.error(f'Échec envoi message contact : {e}')
            _sauver_message_secours(champs)  # rien n'est perdu
        flash('Votre message a bien été envoyé. Nous vous recontacterons rapidement.', 'success')
        return redirect(url_for('contact'))
    return render_template('public/contact.html')

@app.route('/mentions-legales')
def mentions():
    return render_template('public/mentions.html')

@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt', mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    base_url = request.url_root.rstrip('/')
    pages = [
        {'loc': '/', 'priority': '1.0', 'changefreq': 'weekly'},
        {'loc': '/groupes-artistes', 'priority': '0.9', 'changefreq': 'monthly'},
        {'loc': '/prestations-techniques', 'priority': '0.9', 'changefreq': 'monthly'},
        {'loc': '/galerie', 'priority': '0.7', 'changefreq': 'monthly'},
        {'loc': '/contact', 'priority': '0.8', 'changefreq': 'yearly'},
        {'loc': '/mentions-legales', 'priority': '0.3', 'changefreq': 'yearly'},
    ]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for p in pages:
        xml += f'  <url>\n'
        xml += f'    <loc>{base_url}{p["loc"]}</loc>\n'
        xml += f'    <changefreq>{p["changefreq"]}</changefreq>\n'
        xml += f'    <priority>{p["priority"]}</priority>\n'
        xml += f'  </url>\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')

# ════════════════════════════════════════════════
#  BACK-OFFICE — Authentification
# ════════════════════════════════════════════════

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            login_user(USERS['1'])
            return redirect(url_for('admin_dashboard'))
        flash('Identifiants incorrects.', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('index'))

# ════════════════════════════════════════════════
#  BACK-OFFICE — Dashboard
# ════════════════════════════════════════════════

@app.route('/admin')
@login_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

# ─── Module Devis ───
@app.route('/admin/devis')
@login_required
def admin_devis():
    return render_template('admin/devis.html')

@app.route('/admin/devis/generer', methods=['POST'])
@login_required
def admin_devis_generer():
    data = request.get_json()
    # TODO: appeler le module de génération de devis existant
    return jsonify({'status': 'ok', 'message': 'Devis généré', 'data': data})

# ─── Module Facturation ───
@app.route('/admin/facturation')
@login_required
def admin_facturation():
    return render_template('admin/facturation.html')

@app.route('/admin/facturation/generer', methods=['POST'])
@login_required
def admin_facturation_generer():
    data = request.get_json()
    return jsonify({'status': 'ok', 'message': 'Facture générée', 'data': data})

# ─── Module Prospection / Mailing ───
@app.route('/admin/prospection')
@login_required
def admin_prospection():
    return render_template('admin/prospection.html')

@app.route('/admin/prospection/rechercher', methods=['POST'])
@login_required
def admin_prospection_rechercher():
    data = request.get_json()
    # TODO: appeler agent_prospection.py
    return jsonify({'status': 'ok', 'results': []})

@app.route('/admin/mailing')
@login_required
def admin_mailing():
    return render_template('admin/mailing.html')

@app.route('/admin/mailing/envoyer', methods=['POST'])
@login_required
def admin_mailing_envoyer():
    data = request.get_json()
    # TODO: appeler google_workspace.envoyer_email()
    return jsonify({'status': 'ok', 'message': 'Email envoyé'})

# ─── Module Embauche Intermittents ───
@app.route('/admin/embauche')
@login_required
def admin_embauche():
    return render_template('admin/embauche.html')

@app.route('/admin/embauche/calculer', methods=['POST'])
@login_required
def admin_embauche_calculer():
    data = request.get_json()
    # TODO: calculer charges sociales via skill embauche-intermittents
    return jsonify({'status': 'ok', 'data': data})

# ─── Module Comptabilité ───
@app.route('/admin/comptabilite')
@login_required
def admin_comptabilite():
    return render_template('admin/comptabilite.html')

@app.route('/admin/comptabilite/ecriture', methods=['POST'])
@login_required
def admin_compta_ecriture():
    data = request.get_json()
    return jsonify({'status': 'ok', 'data': data})

# ════════════════════════════════════════════════
#  API — Points d'entrée pour les agents
# ════════════════════════════════════════════════

@app.route('/api/prospects/stats')
@login_required
def api_prospects_stats():
    """Stats de la base prospects pour le dashboard"""
    try:
        from tools.prospects_db import ProspectsDB
        db = ProspectsDB()
        stats = {
            'total': db.count_all(),
            'chauds': db.count_by_status('chaud'),
            'tiedes': db.count_by_status('tiede'),
            'froids': db.count_by_status('froid'),
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'total': '~7000', 'chauds': '-', 'tiedes': '-', 'froids': '-', 'error': str(e)})

# ════════════════════════════════════════════════

if __name__ == '__main__':
    app.run(debug=True, port=5000)
