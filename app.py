"""Flask Pokédex backed by the public PokéAPI v2."""

from __future__ import annotations

import re
import threading
import time
from typing import Any

import requests
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__, static_folder="public/static")
API_ROOT = "https://pokeapi.co/api/v2"
PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 100
CACHE_TTL_SECONDS = 300
_cache: dict[str, tuple[float, Any]] = {}
_cache_lock = threading.Lock()

STAT_LABELS = {
    "hp": "HP",
    "attack": "攻擊",
    "defense": "防禦",
    "special-attack": "特攻",
    "special-defense": "特防",
    "speed": "速度",
}


class PokeAPIError(Exception):
    """A friendly, expected failure while contacting PokéAPI."""


def _get_json(path: str) -> Any:
    key = f"{API_ROOT}/{path.lstrip('/')}"
    now = time.monotonic()
    with _cache_lock:
        cached = _cache.get(key)
        if cached and cached[0] > now:
            return cached[1]
    try:
        response = requests.get(key, timeout=(3.05, 10))
        if response.status_code == 404:
            raise PokeAPIError("找不到這筆寶可夢資料。")
        response.raise_for_status()
        payload = response.json()
    except PokeAPIError:
        raise
    except (requests.RequestException, ValueError) as exc:
        raise PokeAPIError("目前無法連線至寶可夢資料服務，請稍後再試。") from exc
    with _cache_lock:
        _cache[key] = (time.monotonic() + CACHE_TTL_SECONDS, payload)
    return payload


def _pokemon_id(url: str) -> int:
    match = re.search(r"/pokemon/(\d+)/?$", url)
    return int(match.group(1)) if match else 0


def _image_for(pokemon: dict[str, Any]) -> str:
    sprites = pokemon.get("sprites") or {}
    official = (sprites.get("other") or {}).get("official-artwork") or {}
    return official.get("front_default") or sprites.get("front_default") or ""


def _extract_stats(pokemon: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in pokemon.get("stats", []):
        raw_name = (item.get("stat") or {}).get("name", "")
        base_val = int(item.get("base_stat", 0))
        result.append({
            "key": raw_name,
            "label": STAT_LABELS.get(raw_name, raw_name),
            "value": base_val,
            "percent": min(max(round(base_val / 255 * 100), 4), 100),
        })
    return result


@app.get("/")
def index():
    try:
        limit = min(max(int(request.args.get("limit", PAGE_SIZE_DEFAULT)), 1), PAGE_SIZE_MAX)
        offset = max(int(request.args.get("offset", 0)), 0)
    except (TypeError, ValueError):
        limit, offset = PAGE_SIZE_DEFAULT, 0
    try:
        data = _get_json(f"pokemon?limit={limit}&offset={offset}")
    except PokeAPIError as exc:
        return render_template("error.html", message=str(exc)), 503
    entries = []
    for item in data.get("results", []):
        pid = _pokemon_id(item.get("url", ""))
        entries.append({
            "id": pid,
            "name": item.get("name", ""),
            "image": (
                f"https://raw.githubusercontent.com/PokeAPI/sprites/master/"
                f"sprites/pokemon/other/official-artwork/{pid}.png"
                if pid > 0 else ""
            ),
        })
    return render_template(
        "index.html",
        pokemon=entries,
        limit=limit,
        offset=offset,
        total=data.get("count", 0),
        previous=offset > 0,
        next_page=offset + limit < data.get("count", 0),
    )


@app.get("/search")
def search():
    query = request.args.get("q", "").strip().lower()
    if not query:
        return render_template("error.html", message="請輸入英文名稱或全國圖鑑編號。"), 400
    identifier = query if query.isdecimal() else re.sub(r"\s+", "-", query)
    return redirect(url_for("detail", identifier=identifier))


@app.get("/pokemon/<identifier>")
def detail(identifier: str):
    identifier = identifier.strip().lower()
    if not (identifier.isdecimal() or re.fullmatch(r"[a-z0-9-]+", identifier)):
        return render_template("error.html", message="請輸入有效的英文名稱或圖鑑編號。"), 400
    try:
        pokemon = _get_json(f"pokemon/{identifier}")
    except PokeAPIError as exc:
        code = 404 if "找不到" in str(exc) else 503
        return render_template("error.html", message=str(exc)), code

    chinese_name = None
    species_url = (pokemon.get("species") or {}).get("url", "")
    species_match = re.search(r"/pokemon-species/(\d+)/?$", species_url)
    species_id = int(species_match.group(1)) if species_match else 0
    if species_id:
        try:
            species = _get_json(f"pokemon-species/{species_id}")
            for item in species.get("names", []):
                if (item.get("language") or {}).get("name") == "zh-Hant":
                    chinese_name = item.get("name")
                    break
        except PokeAPIError:
            pass

    types = [(t.get("type") or {}).get("name", "") for t in pokemon.get("types", [])]
    abilities = [(a.get("ability") or {}).get("name", "").replace("-", " ") for a in pokemon.get("abilities", [])]
    moves = [(m.get("move") or {}).get("name", "").replace("-", " ") for m in pokemon.get("moves", [])[:8]]
    height_m = round(int(pokemon.get("height") or 0) / 10, 1)
    weight_kg = round(int(pokemon.get("weight") or 0) / 10, 1)
    stats = _extract_stats(pokemon)

    return render_template(
        "detail.html",
        pokemon=pokemon,
        image=_image_for(pokemon),
        chinese_name=chinese_name,
        types=types,
        abilities=abilities,
        moves=moves,
        height_m=height_m,
        weight_kg=weight_kg,
        stats=stats,
    )


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", message="找不到這個頁面或寶可夢。"), 404


if __name__ == "__main__":
    app.run(debug=False)
