# Tatoma · Planificador de producción

Aplicación web para planificar pedidos de fabricación, detectar cuellos de botella y consultar la ocupación semanal de la planta. El frontend está servido por FastAPI en el mismo origen; los datos y la autenticación se gestionan en el backend.

## Requisitos

- Python 3.13 recomendado (compatible con las dependencias fijadas).

## Instalación y ejecución

Desde la raíz del repositorio, en PowerShell:

```powershell
cd tatoma_ctp_backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

En Linux o macOS, activa el entorno con `source .venv/bin/activate` después de crearlo con `python3 -m venv .venv`; el resto de comandos es igual.

Abre `http://127.0.0.1:8000`. Uvicorn ejecuta FastAPI, que sirve tanto la aplicación como `/api/v1`; no hace falta iniciar un servidor frontend aparte. Ejecuta el comando desde `tatoma_ctp_backend`: la base local `tatoma_ctp.db` se crea allí al iniciar. En la primera ejecución se crean los usuarios `admin`, `planner` y `viewer`, con contraseñas de desarrollo `admin123`, `planner123` y `viewer123` si no se han definido variables de entorno.

## Ejecución en un servidor

Para aceptar conexiones externas, configura las variables de entorno antes de iniciar Uvicorn. En PowerShell:

```powershell
$env:APP_ENV = "production"
$env:TATOMA_SECRET_KEY = (python -c "import secrets; print(secrets.token_urlsafe(48))")
$env:TATOMA_ADMIN_PASSWORD = "<contraseña-fuerte>"
$env:TATOMA_PLANNER_PASSWORD = "<contraseña-fuerte>"
$env:TATOMA_VIEWER_PASSWORD = "<contraseña-fuerte>"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Usa contraseñas fuertes y no compartas la clave ni las contraseñas. En Linux o macOS, define las mismas variables con `export VARIABLE=valor`. La clave JWT debe tener al menos 32 caracteres.

En producción, publica el servicio detrás de un proxy HTTPS y configura el proxy para admitir WebSockets en `/api/v1/ws/plant`. Si frontend y API se alojan en orígenes diferentes, define `TATOMA_CORS_ORIGINS` con una lista separada por comas y configura `window.TATOMA_API_URL` antes de cargar `planta/js/config.js`. La misma URL relativa funciona automáticamente cuando se sirven desde el mismo origen.

Las variables `TATOMA_ADMIN_PASSWORD`, `TATOMA_PLANNER_PASSWORD` y `TATOMA_VIEWER_PASSWORD` se aplican al crear la base de datos por primera vez. Cambiar esas variables después no modifica usuarios ya existentes.

## Verificación

- Estado: `GET /health`.
- Documentación interactiva: `/docs`.
- Contratos y modelos: [docs/endpoints.md](docs/endpoints.md).
- Requisitos funcionales: [docs/requisitos.md](docs/requisitos.md).