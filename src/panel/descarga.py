"""Descarga de velas OHLCV desde la API publica de Binance (RF-D1, RF-D2).

Se eligio Binance sobre CoinGecko y yfinance por tres razones medibles: no exige
clave de API, entrega OHLCV completo (yfinance no da volumen consistente para
cripto) y permite paginar historia profunda sin limite de llamadas gratuito
(CoinGecko limita el historico horario a los ultimos 90 dias en el plan gratuito).

Lo que se pierde: dependemos de un solo exchange, asi que los precios son los de
Binance y no un promedio de mercado. Para un problema de deteccion de giros eso
es aceptable y hay que decirlo en el informe.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

from contracts.config import SIMBOLOS

BASE_URL = "https://api.binance.com/api/v3/klines"
LIMITE_POR_LLAMADA = 1000
REINTENTOS = 4

COLUMNAS_CRUDAS = [
    "apertura_ms",
    "apertura",
    "maximo",
    "minimo",
    "cierre",
    "volumen",
    "cierre_ms",
    "volumen_cotizado",
    "operaciones",
    "volumen_comprador_base",
    "volumen_comprador_cotizado",
    "ignorar",
]


def _pedir(simbolo: str, intervalo: str, desde_ms: int) -> list[list]:
    """Una llamada a la API, con reintentos y espera creciente.

    Los reintentos existen porque un 429 o un corte de red a mitad de una descarga
    de miles de velas dejaria el panel incompleto sin que nadie lo note.
    """
    parametros = {
        "symbol": simbolo,
        "interval": intervalo,
        "startTime": desde_ms,
        "limit": LIMITE_POR_LLAMADA,
    }
    ultimo_error: Exception | None = None
    for intento in range(REINTENTOS):
        try:
            respuesta = requests.get(BASE_URL, params=parametros, timeout=30)
            respuesta.raise_for_status()
            return respuesta.json()
        except Exception as error:  # noqa: BLE001 - se reintenta cualquier fallo de red
            ultimo_error = error
            time.sleep(2**intento)
    raise RuntimeError(
        f"fallaron {REINTENTOS} intentos de descarga de {simbolo}: {ultimo_error}"
    )


def descargar_activo(activo: str, intervalo: str, desde: str = "2017-01-01") -> pd.DataFrame:
    """Historia completa de un activo desde `desde` hasta ahora.

    Devuelve un DataFrame indexado por fecha UTC con las cinco columnas OHLCV.
    """
    simbolo = SIMBOLOS[activo]
    desde_ms = int(pd.Timestamp(desde, tz="UTC").timestamp() * 1000)
    ahora_ms = int(time.time() * 1000)

    bloques: list[list[list]] = []
    while desde_ms < ahora_ms:
        bloque = _pedir(simbolo, intervalo, desde_ms)
        if not bloque:
            break
        bloques.append(bloque)
        ultimo_cierre_ms = int(bloque[-1][6])
        if ultimo_cierre_ms <= desde_ms:
            break
        desde_ms = ultimo_cierre_ms + 1
        if len(bloque) < LIMITE_POR_LLAMADA:
            break
        time.sleep(0.12)  # cortesia con el rate limit publico

    if not bloques:
        raise RuntimeError(f"la API no devolvio ninguna vela para {activo} ({simbolo})")

    crudo = pd.DataFrame([fila for bloque in bloques for fila in bloque], columns=COLUMNAS_CRUDAS)
    marco = pd.DataFrame(
        {
            "fecha": pd.to_datetime(crudo["apertura_ms"], unit="ms", utc=True),
            "apertura": crudo["apertura"].astype(float),
            "maximo": crudo["maximo"].astype(float),
            "minimo": crudo["minimo"].astype(float),
            "cierre": crudo["cierre"].astype(float),
            "volumen": crudo["volumen"].astype(float),
        }
    )
    marco = marco.drop_duplicates(subset="fecha").set_index("fecha").sort_index()

    # La ultima vela suele estar en curso: sus valores cambian hasta que cierra.
    # Incluirla haria que dos descargas del mismo dia produjeran paneles distintos.
    ahora = pd.Timestamp.now(tz="UTC")
    duracion = _duracion_intervalo(intervalo)
    marco = marco[marco.index + duracion <= ahora]

    return marco


def _duracion_intervalo(intervalo: str) -> pd.Timedelta:
    unidades = {"m": "min", "h": "h", "d": "D", "w": "W"}
    numero, sufijo = intervalo[:-1], intervalo[-1]
    return pd.Timedelta(f"{numero}{unidades[sufijo]}")


def descargar_todos(
    intervalo: str,
    destino: Path,
    desde: str = "2017-01-01",
) -> dict[str, pd.DataFrame]:
    """Descarga los seis activos y deja el crudo en disco con su manifiesto.

    El manifiesto (RF-D2) registra fuente, fecha de descarga, rango y hash. Sin el
    no hay forma de saber si una figura del informe salio de estos datos o de otros
    descargados una semana antes.
    """
    destino.mkdir(parents=True, exist_ok=True)
    series: dict[str, pd.DataFrame] = {}
    manifiesto: dict[str, dict] = {
        "fuente": BASE_URL,
        "descargado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "intervalo": intervalo,
        "activos": {},
    }

    for activo in SIMBOLOS:
        marco = descargar_activo(activo, intervalo, desde)
        ruta = destino / f"{activo}_{intervalo}.parquet"
        marco.to_parquet(ruta)
        series[activo] = marco
        manifiesto["activos"][activo] = {
            "simbolo": SIMBOLOS[activo],
            "archivo": ruta.name,
            "n": int(len(marco)),
            "desde": marco.index.min().isoformat(),
            "hasta": marco.index.max().isoformat(),
            "sha256": hashlib.sha256(ruta.read_bytes()).hexdigest()[:16],
        }

    (destino / "MANIFEST.json").write_text(
        json.dumps(manifiesto, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return series
