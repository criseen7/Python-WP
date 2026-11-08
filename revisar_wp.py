#!/usr/bin/env python3
"""Revisa sitios WordPress: que respondan y que su ultima nota tenga < 24 h.

Uso: python revisar_wp.py sitios.txt
Una URL por linea (ej. https://ejemplo.com); ignora lineas vacias y con #.
"""
import json
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

MAX_HORAS, TIMEOUT = 24, 10
UA = "Mozilla/5.0 (compatible; WP-check/1.0)"


def ultima_nota(base):
    if "://" not in base:
        base = "https://" + base
    url = urljoin(base.rstrip("/") + "/", "wp-json/wp/v2/posts?per_page=1&_fields=date_gmt")
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urlopen(req, timeout=TIMEOUT) as r:
        posts = json.load(r)
    if not posts:
        raise ValueError("sin notas publicadas")
    fecha = datetime.fromisoformat(posts[0]["date_gmt"].replace("Z", "+00:00"))
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


def revisar(base):
    try:
        fecha = ultima_nota(base)
    except HTTPError as e:
        return f"HTTP {e.code}"
    except (URLError, OSError) as e:
        return f"sin respuesta ({getattr(e, 'reason', e)})"
    except (ValueError, KeyError, TypeError) as e:
        return f"API invalida ({e})"
    horas = (datetime.now(timezone.utc) - fecha).total_seconds() / 3600
    return None if horas < MAX_HORAS else f"ultima nota hace {horas:.1f} h"


def main():
    if len(sys.argv) != 2:
        sys.exit("Uso: python revisar_wp.py sitios.txt")
    with open(sys.argv[1], encoding="utf-8") as f:
        sitios = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    fallos = [(s, e) for s in sitios if (e := revisar(s))]
    print(f"{len(sitios) - len(fallos)}/{len(sitios)} OK; {len(fallos)} con fallas")
    if fallos:
        print("\nFallan:")
        print("\n".join(f"- {s}: {e}" for s, e in fallos))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
