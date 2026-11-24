from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Tus datos (identidad, entradas, biblioteca) no viven junto al código: así el código se
# puede compartir sin ellos. Se buscan, por orden:
#   1. AGENT_DATOS_NETWORKING en el .env, si lo pones;
#   2. `mis-datos/` en la raíz del proyecto: los tuyos, fuera de git;
#   3. `datos-ejemplo/`: una persona inventada, para probar la app recién descargada.
_PROYECTO = Path(__file__).resolve().parents[3]
_VARIABLE = "AGENT_DATOS_NETWORKING"
if not os.getenv(_VARIABLE):
    _mios = _PROYECTO / "mis-datos"
    os.environ[_VARIABLE] = str(_mios if _mios.is_dir() else _PROYECTO / "datos-ejemplo")
DATOS: Path = Path(os.environ[_VARIABLE]).expanduser().resolve()

# Los contactos, candidatos, plantillas y pendientes: tus `entradas/`. AGENT_DATA_PATH
# solo sirve para apuntarlas aparte (lo usan los tests).
_RAW_DATA_PATH = os.getenv("AGENT_DATA_PATH", str(DATOS / "entradas"))
DATA_PATH: Path = Path(_RAW_DATA_PATH).expanduser().resolve()

APP_PORT: int = int(os.getenv("APP_PORT", "8080"))


def validate_data_path() -> None:
    if not DATA_PATH.exists():
        raise RuntimeError(
            f"AGENT_DATA_PATH no existe: {DATA_PATH}\n"
            f"Revisa la variable AGENT_DATA_PATH en .env."
        )
    if not DATA_PATH.is_dir():
        raise RuntimeError(f"AGENT_DATA_PATH no es un directorio: {DATA_PATH}")
    # Sentinela: los contactos son el dato propio nuclear de networking.
    if not (DATA_PATH / "contactos").exists():
        raise RuntimeError(
            f"AGENT_DATA_PATH no apunta a los datos de networking "
            f"(falta contactos/): {DATA_PATH}"
        )
