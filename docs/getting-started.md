# Getting started

## Install

```bash
pip install glpi-api-hero
```

Python 3.10 or newer is required.

## Open a session

Every model needs an open session. The simplest way is the context manager, which also closes the session:

```python
from glpi_api_hero import Glpi

with Glpi.session("https://glpi.example.org/apirest.php", "APP_TOKEN", user_token="USER_TOKEN"):
    ...
```

Use `username=` and `password=` instead of `user_token=` to log in with credentials. TLS certificates are verified
by default; use `REQUESTS_CA_BUNDLE` for a private certificate authority.

Without the context manager:

```python
Glpi.connect(url, app_token, user_token="USER_TOKEN")
try:
    ...
finally:
    Glpi.disconnect()
```

The API URL must be absolute (`http://` or `https://`), without credentials, query or fragment. Redirects are not
followed (tokens must never reach another host): configure the final URL. Plain `http` raises a warning.

## Profile and entity

```python
Glpi.set_profile_entity(profiles_id=4, entities_id=1, is_recursive=True)
```

## Using a model

Models are never instantiated: every method is a class method.

```python
from glpi_api_hero.assets import Computer

computer = Computer.get(12)                       # dict
Computer.update(12, {"comment": "Rack 3"})        # None
Computer.get_network_ports(12)                    # list[dict]
```

The session is global to the process and is not safe for threads that need different profiles or entities.
