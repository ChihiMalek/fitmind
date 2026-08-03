"""
providers.py — authentification externe (demo aujourd'hui, reelle plus tard).

AuthProvider est un Protocol : n'importe quelle classe qui expose
authenticate(credentials) -> ProviderUserData peut etre enregistree dans
PROVIDERS sans qu'auth_service.py n'ait jamais besoin de changer — voir
ARCHITECTURE_AUTH_v1.md §6 (extensibilite OAuth/JWT/API REST). Ce fichier
ne connait ni SQLite ni st.session_state : un provider authentifie aupres
d'un fournisseur externe (ou, ici, simule ce fournisseur) et retourne des
donnees brutes, sans jamais persister ni gerer de session lui-meme.

DemoGoogleProvider reproduit EXACTEMENT le comportement actuel de app.py
(accepte toute chaine contenant '@', aucune verification d'identite
reelle). Ce n'est PAS un vrai OAuth Google — aucune API externe n'est
appelee. Documente explicitement comme demonstration a chaque endroit ou
il apparait.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from auth.exceptions import InvalidCredentials


@dataclass
class ProviderUserData:
    """Donnees renvoyees par un provider apres authentification reussie."""

    email: str
    username: str
    provider_uid: str


@runtime_checkable
class AuthProvider(Protocol):
    """Contrat que doit respecter tout provider d'authentification externe."""

    def authenticate(self, credentials: dict) -> ProviderUserData:
        """
        Authentifie aupres du fournisseur externe et retourne les donnees
        utilisateur associees.

        Raises:
            auth.exceptions.InvalidCredentials: si l'authentification echoue.
        """
        ...


class DemoGoogleProvider:
    """
    Provider de DEMONSTRATION UNIQUEMENT.

    Reproduit le comportement actuel de app.py : toute adresse contenant
    '@' est acceptee, sans verification d'identite reelle aupres de
    Google. Aucun appel a une API externe, aucun OAuth reel.

    A remplacer par un vrai GoogleOAuthProvider (respectant le meme
    Protocol AuthProvider) le jour ou une authentification Google reelle
    est necessaire — auth_service.py n'aurait alors aucune ligne a changer,
    seul le registre PROVIDERS serait mis a jour. Voir
    ARCHITECTURE_AUTH_v1.md §6.
    """

    def authenticate(self, credentials: dict) -> ProviderUserData:
        """
        Authentifie de maniere simulee : accepte toute adresse contenant
        '@', sans verification d'identite reelle (voir docstring de classe).

        Args:
            credentials: dict attendu avec une cle "email".

        Raises:
            InvalidCredentials: si "email" est absent ou ne contient pas '@'.
        """
        email = (credentials or {}).get("email", "") or ""
        if "@" not in email:
            raise InvalidCredentials("Email invalide pour la connexion Google (demo).")
        username = email.split("@")[0]
        return ProviderUserData(email=email, username=username, provider_uid=email)


# Registre des providers disponibles. auth_service.py ne doit jamais
# instancier directement un provider : il passe systematiquement par ce
# dict, cle par un nom stable (correspond a users.auth_provider en base).
PROVIDERS: dict = {
    "google_demo": DemoGoogleProvider(),
}
