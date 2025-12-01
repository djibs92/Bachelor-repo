from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialisation du Limiter
# key_func=get_remote_address : Limite basée sur l'adresse IP du client
limiter = Limiter(key_func=get_remote_address)
