"""
auth_service.py — orchestration metier de l'authentification.

Seul fichier autorise a coordonner security.py + providers.py + les
repositories de database/repositories/. N'importe jamais sqlite3, ne fait
jamais de SQL, et ne retourne jamais de tuple (ok, message) : toute erreur
d'authentification est une exception de auth/exceptions.py.

Independance vis-a-vis du mecanisme de session (revue post-Etape 3) :
auth_service N'IMPORTE PLUS auth.session_manager et ne cree, ne lit, ni ne
detruit jamais de session. Son role s'arrete a : authentifier, retourner
un User, ecrire les audit logs, mettre a jour last_login_at et
failed_login_attempts. La creation/destruction de session est de la
responsabilite exclusive de l'appelant (app.py a l'Etape 4, via
auth.session_manager ; demain, une API REST via un JWT ; une application
mobile via un autre mecanisme) — sans jamais avoir a modifier ce fichier.
Voir ARCHITECTURE_AUTH_v1.md §6.

Reference : ARCHITECTURE_AUTH_v1.md §2, §3, §6.

Perimetre audit de cette etape (voir consignes Etape 3) : seuls REGISTER,
LOGIN (represente par AuthEventType.LOGIN_SUCCESS) et LOGOUT sont
journalises. Les autres valeurs de AuthEventType (LOGIN_FAILED,
ACCOUNT_LOCKED, ...) existent deja dans auth/enums.py pour usage futur,
mais ne sont volontairement pas emises ici — un elargissement du perimetre
d'audit est une decision separee, pas un oubli.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from auth.auth_config import LOCKOUT_DURATION_MINUTES, MAX_FAILED_LOGIN_ATTEMPTS
from auth.enums import AuthEventType, Role
from auth.exceptions import AccountDeleted, DuplicateEmail, InvalidCredentials, UserLocked
from auth.providers import PROVIDERS
from auth.security import (
    hash_password,
    validate_email_format,
    validate_password_strength,
    verify_password,
)
from database.models import User
from database.repositories.auth_log_repository import AuthLogRepository
from database.repositories.user_repository import UserRepository

_user_repo = UserRepository()
_log_repo = AuthLogRepository()


def _is_locked(user: User) -> bool:
    if not user.locked_until:
        return False
    return datetime.fromisoformat(user.locked_until) > datetime.now(timezone.utc)


def register(email: str, password: str, username: str = "") -> User:
    """
    Flux (ARCHITECTURE_AUTH_v1.md §3, diagramme Register) :
    validation email -> validation mot de passe -> recherche utilisateur
    -> hash bcrypt -> creation utilisateur -> audit log REGISTER -> retour User.

    Raises:
        InvalidEmailFormat, WeakPassword: leves par security.py.
        DuplicateEmail: si l'email est deja utilise.
    """
    validate_email_format(email)
    validate_password_strength(password)

    if _user_repo.get_by_email(email) is not None:
        raise DuplicateEmail(f"Un compte existe deja avec l'email {email!r}.")

    password_hash = hash_password(password)
    user = _user_repo.create(email=email, password_hash=password_hash, username=username)
    _log_repo.create(event_type=AuthEventType.REGISTER.value, user_id=user.id)
    return user


def login(email: str, password: str) -> User:
    """
    Flux (ARCHITECTURE_AUTH_v1.md §3, diagramme Login — adapte pour ne
    jamais ouvrir de session, voir docstring de module) :
    recherche utilisateur -> compte supprime ? -> compte verrouille ? ->
    bcrypt.verify() -> (incorrect -> increment des tentatives, verrouillage
    si seuil atteint) / (valide -> remise a zero des tentatives ->
    update_last_login() -> audit log LOGIN) -> retour User.

    N'ouvre JAMAIS de session. L'appelant est responsable de decider quoi
    faire du User retourne (session Streamlit, JWT, autre) — voir
    docstring de module.

    Raises:
        InvalidCredentials: email inconnu OU mot de passe incorrect — la
            meme exception est levee dans les deux cas, deliberement, pour
            ne jamais reveler si un email est enregistre ou non.
        AccountDeleted: le compte a ete supprime (deleted_at non nul).
        UserLocked: trop d'echecs recents, compte temporairement verrouille.
    """
    user = _user_repo.get_by_email(email)
    if user is None:
        raise InvalidCredentials("Email ou mot de passe incorrect.")

    if user.deleted_at is not None:
        raise AccountDeleted("Ce compte a ete supprime.")

    if _is_locked(user):
        raise UserLocked("Compte temporairement verrouille suite a plusieurs echecs de connexion.")

    if not verify_password(password, user.password_hash):
        _user_repo.increment_failed_attempts(user.id)
        refreshed = _user_repo.get_by_id(user.id)
        if refreshed.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            locked_until = (
                datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            ).isoformat()
            _user_repo.set_locked_until(user.id, locked_until)
        raise InvalidCredentials("Email ou mot de passe incorrect.")

    _user_repo.reset_failed_attempts(user.id)
    _user_repo.update_last_login(user.id)
    user = _user_repo.get_by_id(user.id)

    _log_repo.create(event_type=AuthEventType.LOGIN_SUCCESS.value, user_id=user.id)
    return user


def logout(user_id: Optional[int] = None) -> None:
    """
    Ecrit uniquement l'audit log LOGOUT — n'effectue aucune operation de
    session (ni lecture, ni destruction). auth_service n'a plus aucun
    moyen de savoir "qui est actuellement connecte" puisqu'il n'importe
    plus auth.session_manager : c'est a l'appelant de connaitre cette
    identite (via sa propre gestion de session/token) et de la fournir ici.

    L'appelant reste responsable d'invalider la session apres cet appel
    (ex. app.py appelle auth.session_manager.clear_session() lui-meme a
    l'Etape 4).

    Args:
        user_id: identifiant de l'utilisateur qui se deconnecte, ou None
            si inconnu (n'empeche pas l'ecriture du log).
    """
    _log_repo.create(event_type=AuthEventType.LOGOUT.value, user_id=user_id)


def login_with_provider(provider_name: str, credentials: dict) -> User:
    """
    Flux (ARCHITECTURE_AUTH_v1.md §3, diagramme Google Demo — adapte pour
    ne jamais ouvrir de session, voir docstring de module) :
    Provider.authenticate() -> get_by_email() -> creation automatique si
    necessaire -> update_last_login() -> audit log -> retour User.

    N'ouvre JAMAIS de session (memes raisons que login()). auth_service
    n'instancie jamais un provider directement : il passe systematiquement
    par le registre auth.providers.PROVIDERS.

    Raises:
        KeyError: provider_name inconnu du registre.
        InvalidCredentials: leve par le provider si l'authentification
            externe echoue.
        AccountDeleted: le compte associe a cet email a ete supprime.
    """
    provider = PROVIDERS[provider_name]
    provider_data = provider.authenticate(credentials)

    user = _user_repo.get_by_email(provider_data.email)
    if user is None:
        # role=Role.CLIENT.value explicite (pas implicite via le defaut du
        # repository) : un compte cree via un provider externe ne doit
        # JAMAIS pouvoir devenir admin, meme si le defaut de create()
        # venait a changer un jour pour un autre appelant.
        user = _user_repo.create(
            email=provider_data.email,
            password_hash="",
            username=provider_data.username,
            role=Role.CLIENT.value,
            auth_provider=provider_name,
        )

    if user.deleted_at is not None:
        raise AccountDeleted("Ce compte a ete supprime.")

    _user_repo.update_last_login(user.id)
    user = _user_repo.get_by_id(user.id)

    _log_repo.create(event_type=AuthEventType.LOGIN_SUCCESS.value, user_id=user.id,
                      detail=f"via {provider_name}")
    return user


def change_password(user_id: int, old_password: str, new_password: str) -> None:
    """
    Flux : recherche utilisateur -> verification de l'ancien mot de passe
    -> validation du nouveau -> hash bcrypt -> persistance.

    Ne journalise pas d'evenement a cette etape (perimetre audit explicite
    de l'Etape 3 : REGISTER / LOGIN / LOGOUT uniquement — voir docstring
    de module). AuthEventType.PASSWORD_CHANGED existe deja pour un usage
    futur.

    Raises:
        InvalidCredentials: utilisateur introuvable/supprime, ou ancien
            mot de passe incorrect.
        WeakPassword: le nouveau mot de passe ne respecte pas la politique.
    """
    user = _user_repo.get_by_id(user_id)
    if user is None or user.deleted_at is not None:
        raise InvalidCredentials("Utilisateur introuvable.")
    if not verify_password(old_password, user.password_hash):
        raise InvalidCredentials("Ancien mot de passe incorrect.")

    validate_password_strength(new_password)
    _user_repo.update_password_hash(user_id, hash_password(new_password))


def to_session_dict(user: User) -> dict:
    """
    Convertit un User (dataclass complet, avec password_hash) en dict pret
    a l'affichage — EXACTEMENT la forme actuellement produite par
    do_login()/do_register() dans app.py pour les cles reellement lues
    ailleurs dans le code (email, name, initials, role — verifie contre
    app.py : user['email'], user['name'], user.get('initials', ...),
    user.get('role', ...)), de sorte que dashboard.render() et le reste de
    app.py continuent de fonctionner sans aucune modification
    (ARCHITECTURE_AUTH_v1.md §8). Aucune cle en plus, aucune cle en moins.

    Ne contient jamais password_hash ni aucun champ sensible. Ne contient
    pas non plus l'id interne : ce dict est destine a l'affichage (UI),
    l'id interne n'est pas necessaire aux appelants actuels et n'a pas a
    transiter par ce contrat pour rester une correspondance exacte avec
    la structure historique de app.py.
    """
    name = user.username or user.email.split("@")[0]
    initials = "".join(w[0] for w in name.strip().split())[:2].upper() or name[0].upper()
    return {
        "email": user.email,
        "name": name,
        "initials": initials,
        "role": user.role,
    }


def list_users(include_deleted: bool = False) -> List[User]:
    """
    Retourne tous les utilisateurs enregistres.

    Ajoutee a l'Etape 4 : le panneau admin "Utilisateurs" de app.py listait
    st.session_state.users_db, supprime par cette etape. Simple delegation
    au repository, aucune logique metier — expose ici uniquement pour que
    app.py n'ait jamais besoin d'importer UserRepository directement
    (respect strict de la couche Services : UI -> Services -> Repositories).
    """
    return _user_repo.list_users(include_deleted=include_deleted)


def ensure_seed_account(email: str, password: str, username: str, role: str) -> User:
    """
    Cree un compte de demonstration/seed avec un role EXPLICITE, de maniere
    idempotente : si un compte existe deja avec cet email, il n'est jamais
    modifie (ni mot de passe, ni role) et est simplement retourne tel quel
    — jamais ecrase (ARCHITECTURE_AUTH_v1.md §9).

    A NE JAMAIS exposer a un formulaire public : contrairement a
    register(), cette fonction accepte un role arbitraire (y compris
    'admin'). Reservee au seeding controle des comptes de demonstration au
    demarrage de l'application (voir app.py, Etape 4) — register() reste
    la seule fonction utilisable par un formulaire d'inscription, et ne
    cree jamais que des comptes 'client'.

    Raises:
        InvalidEmailFormat, WeakPassword: memes regles que register().
    """
    validate_email_format(email)
    validate_password_strength(password)

    existing = _user_repo.get_by_email(email)
    if existing is not None:
        return existing

    password_hash = hash_password(password)
    return _user_repo.create(email=email, password_hash=password_hash,
                              username=username, role=role)
