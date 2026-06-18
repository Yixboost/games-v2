from dataclasses import dataclass, field


@dataclass
class Role:
    name: str
    permissions: set[str] = field(default_factory=set)


class PermissionRegistry:
    def __init__(self):
        self._permissions: set[str] = set()
        self._roles: dict[str, Role] = {}

    def register_permission(self, permission: str) -> None:
        self._permissions.add(permission)

    def register_role(self, role: Role) -> None:
        self._roles[role.name] = role
        self._permissions.update(role.permissions)

    def role_has_permission(self, role_name: str, permission: str) -> bool:
        role = self._roles.get(role_name)
        return bool(role and permission in role.permissions)

    def user_has_permission(self, user, permission: str) -> bool:
        if user is None:
            return False

        return self.role_has_permission(getattr(user, "role", ""), permission)

    def clear(self) -> None:
        self._permissions.clear()
        self._roles.clear()


permission_registry = PermissionRegistry()
