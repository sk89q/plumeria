from functools import wraps
from . import config
from .config import set_of
from .command import AuthorizationError

owner_ids = config.create("perms", "admin_users", set_of(str), fallback="")


def has_role_in(user, roles):
    for role in user.roles:
        if role.name in roles:
            return True
    return False


def is_owner(user):
    return user.id in owner_ids()


def is_server_admin(user):
    for role in user.roles:
        if role.name == "bot-admin":
            return True
    return False


def owners_only(f):
    @wraps(f)
    async def wrapper(message, *args, **kwargs):
        if is_owner(message.author):
            return await f(message, *args, **kwargs)
        else:
            raise AuthorizationError()

    wrapper.owners_only = True
    return wrapper


def server_admins_only(f):
    @wraps(f)
    async def wrapper(message, *args, **kwargs):
        if is_server_admin(message.author):
            return await f(message, *args, **kwargs)
        else:
            raise AuthorizationError()

    wrapper.server_admins_only = True
    return wrapper


def roles_only(*roles):
    roles = set(roles)

    def inner(f):
        @wraps(f)
        async def wrapper(message, *args, **kwargs):
            if has_role_in(message.author, roles):
                return await f(message, *args, **kwargs)
            else:
                raise AuthorizationError()

        wrapper.server_admins_only = True
        return wrapper

    return inner
