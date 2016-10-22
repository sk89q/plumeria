from typing import Optional, List, Mapping

from plumeria.transport import User

NO_PROVIDER_ERROR = "The bot doesn't have a plugin enabled that allows storing user preferences."


class Preference:
    def __init__(self, name, type=str, fallback=None, comment=None, private=True):
        self.name = name
        self.type = type
        self.fallback = fallback
        self.comment = "\n".join((" " + s) for s in comment.splitlines()) if comment else None
        self.private = private

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class PreferencesProvider:
    async def get_all(self, user: User) -> Mapping[str, str]:
        return {}

    async def get(self, pref: Preference, user: User) -> str:
        raise KeyError()

    async def put(self, pref: Preference, user: User, value: str):
        raise NotImplementedError(NO_PROVIDER_ERROR)

    async def remove(self, pref: Preference, user: User):
        raise NotImplementedError(NO_PROVIDER_ERROR)


class PreferencesManager:
    def __init__(self):
        self.provider = PreferencesProvider()
        self.preferences = {}

    async def get(self, pref: Preference, user: User):
        return await self.provider.get(pref, user)

    async def put(self, pref: Preference, user: User, value: str):
        if value is not None:
            # make sure the value is valid
            pref.type(value)
        return await self.provider.put(pref, user, value)

    async def remove(self, pref: Preference, user: User):
        return await self.provider.remove(pref, user)

    def create(self, name, type=str, fallback=None, comment=None, private=True) -> Preference:
        preference = Preference(name, type, fallback, comment, private)
        return preference

    def add(self, preference):
        self.preferences[preference.name] = preference
        return preference

    def get_preference(self, name) -> Optional[Preference]:
        return self.preferences[name]

    def get_preferences(self) -> List[Preference]:
        return list(self.preferences.values())

    async def get_all(self, user: User):
        raw_values = await self.provider.get_all(user)
        results = []
        for name, value in raw_values.items():
            if name in self.preferences:
                pref = self.preferences[name]
                results.append((pref, value))
        return results

