import sys
import requests
import ipaddress
import random
from typing import List, Optional, Set, TypedDict

from fp.errors import FreeProxyException  # type:ignore
from fp.fp import FreeProxy  # type:ignore


class ProxyBrokerCriteria(TypedDict, total=False):
    """proxy broker criteria"""

    anonymous: bool
    countryset: Set[str]
    secure: bool
    timeout: float
    search_outside_if_empty: bool


class ProxySettings(TypedDict, total=False):
    """proxy settings"""

    server: str
    bypass: str
    username: str
    password: str


class Proxy(ProxySettings):
    """proxy server information"""

    criteria: ProxyBrokerCriteria


def search_proxy_servers(
    anonymous: bool = True,
    countryset: Optional[Set[str]] = None,
    secure: bool = False,
    timeout: float = 5.0,
    max_shape: int = 5,
    search_outside_if_empty: bool = True,
) -> List[str]:
    """search for proxy servers that match the specified broker criteria

    Args:
        anonymous: whether proxy servers should have minimum level-1 anonymity.
        countryset: admissible proxy servers locations.
        secure: whether proxy servers should support HTTP or HTTPS; defaults to HTTP;
        timeout: The maximum timeout for proxy responses; defaults to 5.0 seconds.
        max_shape: The maximum number of proxy servers to return; defaults to 5.
        search_outside_if_empty: whether countryset should be extended if empty.

    Returns:
        A list of proxy server URLs matching the criteria.

    Example:
        >>> search_proxy_servers(
        ...     anonymous=True,
        ...     countryset={"GB", "US"},
        ...     secure=True,
        ...     timeout=1.0
        ...     max_shape=2
        ... )
        [
            "http://103.10.63.135:8080",
            "http://113.20.31.250:8080",
        ]
    """
    proxybroker = FreeProxy(
        anonym=anonymous,
        country_id=countryset,
        elite=True,
        https=secure,
        timeout=timeout,
    )

    def search_all(
        proxybroker: FreeProxy, k: int, search_outside: bool
    ) -> List[str]:
        candidateset = proxybroker.get_proxy_list(search_outside)
        random.shuffle(candidateset)

        positive = set()

        for address in candidateset:
            setting = {proxybroker.schema: f"http://{address}"}

            try:
                server = proxybroker._FreeProxy__check_if_proxy_is_working(
                    setting
                )

                if not server:
                    continue

                positive.add(server)

                if len(positive) < k:
                    continue

                return list(positive)

            except requests.exceptions.RequestException:
                continue

        n = len(positive)

        if n < k and search_outside:
            proxybroker.country_id = None

            try:
                negative = set(search_all(proxybroker, k - n, False))
            except FreeProxyException:
                negative = set()

            positive = positive | negative

        if not positive:
            raise FreeProxyException("missing proxy servers for criteria")

        return list(positive)

    return search_all(proxybroker, max_shape, search_outside_if_empty)


def is_ipv4_address(address: str) -> bool:
    """If a proxy address conforms to a IPv4 address"""
    try:
        ipaddress.IPv4Address(address)
        return True
    except ipaddress.AddressValueError:
        return False


def dynamic_import(modname: str, message: str = "") -> None:
    """imports a python module at runtime

    Args:
        modname: The module name in the scope
        message: The display message in case of error

    Raises:
        ImportError: If the module cannot be imported at runtime
    """
    if modname not in sys.modules:
        try:
            import importlib  # noqa: F401

            module = importlib.import_module(modname)
            sys.modules[modname] = module
        except ImportError as x:
            raise ImportError(message) from x
