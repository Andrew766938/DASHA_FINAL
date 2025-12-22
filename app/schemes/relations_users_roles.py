from app.schemes.users import SUserGet
from app.schemes.roles import SRoleGet


class SRoleGetWithRels(SRoleGet):
    users: list[SUserGet] | None = None


class SUserGetWithRels(SUserGet):
    role: SRoleGet | None = None
