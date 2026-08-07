"""Simple dependency injection container (Level A).

Registers core services and resolves them as singletons.
No over-engineering: services are wired by type via a factory callable.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Type, TypeVar

T = TypeVar("T")


class DependencyContainer:
    """Minimal DI container with singleton resolution.

    Usage:
        container.register(SecretsManager, lambda c: SecretsManager("secrets.enc"))
        sm = container.resolve(SecretsManager)  # same instance every call
    """

    def __init__(self) -> None:
        self._factories: Dict[Type[Any], Callable[[DependencyContainer], Any]] = {}

    def register(self, service_type: Type[T], factory: Optional[Callable[[DependencyContainer], T]] = None) -> None:
        """Register a service type. If no factory is given, the type is
        instantiated with no arguments (zero-arg constructor)."""
        self._factories[service_type] = factory or (lambda c: service_type())

    def resolve(self, service_type: Type[T]) -> T:
        """Return the singleton instance for the given service type.

        Lazily constructs the instance on first resolve and caches it.
        """
        factory = self._factories.get(service_type)
        if factory is None:
            raise KeyError(f"Service not registered: {service_type.__name__}")
        instance = factory(self)
        self._factories[service_type] = lambda c: instance
        return instance


# Global application container
container = DependencyContainer()
