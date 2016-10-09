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
        if is_owner(message.author) or is_server_admin(message.author):
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
            if is_owner(message.author) or has_role_in(message.author, roles):
                return await f(message, *args, **kwargs)
            else:
                raise AuthorizationError()

        wrapper.server_admins_only = True
        return wrapper

    return inner


def have_all_perms(*perms):
    def decorator(f):
        @wraps(f)
        async def wrapper(message, *args, **kwargs):
            if not hasattr(message.author, "roles"):
                raise AuthorizationError("Permission data has not been loaded.")
            resolved = message.channel.permissions_for(message.author)
            if not resolved:
                raise AuthorizationError("This command cannot be used here because there is no permission information.")
            missing = set()
            for perm in perms:
                if not getattr(resolved, perm):
                    missing.add(perm)
            if len(missing):
                raise AuthorizationError("Missing the following one or more permissions: {}".format(", ".join(perms)))
            return await f(message, *args, **kwargs)

        wrapper.server_admins_only = True
        return wrapper

    return decorator
