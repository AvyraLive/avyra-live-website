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

    # Paths to existing agents
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    AGENTS_DIR = os.path.join(BASE_DIR, '..', 'meta-agent-ia')
