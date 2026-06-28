import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'avyra-live-dev-key-change-in-prod')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'avyra2026')
    MAIL_CONTACT = 'contact@avyra-live.fr'
    PHONE = '07 86 24 38 23'
    SIRET = '105 957 104 00018'
    TVA_INTRA = 'FR 10 105 957 104'
    ADRESSE = '4 Rue Honoré de Balzac, 82000 Montauban'
    SOCIETE = 'SAS AVYRA-LIVE'
    PRESIDENT = 'Jean-Christophe DEJEAN'

    # Formulaire de contact — envoi via l'API Gmail (HTTPS, compatible Render qui bloque le SMTP).
    # Render bloque les ports SMTP (25/465/587) → on utilise le compte de service Google + delegation.
    GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get(
        'GOOGLE_SERVICE_ACCOUNT_FILE', '/etc/secrets/google-service-account.json')
    GOOGLE_DELEGATED_USER = os.environ.get('GOOGLE_DELEGATED_USER', 'fabrice@avyra-live.fr')
    CONTACT_RECIPIENT = os.environ.get('CONTACT_RECIPIENT', 'contact@avyra-live.fr')

    # Paths to existing agents
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    AGENTS_DIR = os.path.join(BASE_DIR, '..', 'meta-agent-ia')
