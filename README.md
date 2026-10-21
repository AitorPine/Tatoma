# Tatoma · Planificador de producción

Aplicación web para planificar pedidos de fabricación, detectar cuellos de botella y consultar la ocupación semanal de la planta. El frontend está servido por FastAPI en el mismo origen; los datos y la autenticación se gestionan en el backend.

## Requisitos

- Python 3.13 recomendado (compatible con las dependencias fijadas).
- Docker Engine y Docker Compose para el despliegue.

## Desarrollo local

Desde la raíz del repositorio:

```bash
cd tatoma_ctp_backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export TATOMA_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Abre `http://127.0.0.1:8000`. FastAPI sirve tanto la aplicación como `/api/v1`; no hace falta iniciar un servidor frontend aparte. La base local `tatoma_ctp.db` se crea al iniciar. En la primera ejecución se crean los usuarios `admin`, `planner` y `viewer`, con contraseñas de desarrollo `admin123`, `planner123` y `viewer123` si no se han definido variables de entorno.

## Despliegue fuera de localhost

1. Copia `.env.example` a `.env` y configura contraseñas fuertes y una clave JWT aleatoria de al menos 32 caracteres. No publiques el archivo `.env`.
2. Inicia el servicio:

```bash
docker compose up --build -d
```

3. Abre `http://<IP-o-dominio-del-servidor>:8000`. El contenedor escucha en `0.0.0.0`; `PORT` cambia el puerto publicado. Los datos sobreviven a recreaciones del contenedor en el volumen `tatoma_data`.

En producción, publica el servicio detrás de un proxy HTTPS y configura el proxy para admitir WebSockets en `/api/v1/ws/plant`. Si frontend y API se alojan en orígenes diferentes, define `TATOMA_CORS_ORIGINS` con una lista separada por comas y configura `window.TATOMA_API_URL` antes de cargar `planta/js/config.js`. La misma URL relativa funciona automáticamente cuando se sirven desde el mismo origen.

Las variables `TATOMA_ADMIN_PASSWORD`, `TATOMA_PLANNER_PASSWORD` y `TATOMA_VIEWER_PASSWORD` se aplican al crear la base de datos por primera vez. Cambiar esas variables después no modifica usuarios ya existentes.

## Verificación

- Estado: `GET /health`.
- Documentación interactiva: `/docs`.
- Contratos y modelos: [docs/endpoints.md](docs/endpoints.md).
- Requisitos funcionales: [docs/requisitos.md](docs/requisitos.md).