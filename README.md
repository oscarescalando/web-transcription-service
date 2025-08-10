# API de Transcripción con FastAPI y Whisper

Este proyecto implementa una API RESTful utilizando Python y FastAPI para transcribir archivos de audio/video y URLs de YouTube a texto. La transcripción se realiza mediante el modelo Whisper de OpenAI.

## Características

-   **API Segura**: Todos los endpoints están protegidos con autenticación de Token Bearer.
-   **Configuración Segura**: El token de la API se gestiona a través de un archivo `.env` para no exponerlo en el código.
-   **API de Transcripción de Archivos**: Endpoint `/upload-file-transcribe` para procesar archivos multimedia.
-   **API de Transcripción de YouTube**: Endpoint `/youtube-url-transcribe` para procesar URLs de videos de YouTube.
-   **Documentación Automática**: Interfaz interactiva de Swagger UI y ReDoc disponible en `/docs` y `/redoc`.

## Prerrequisitos

Antes de comenzar, asegúrate de tener lo siguiente instalado en tu sistema:

1.  **Python 3.8+**
2.  **FFmpeg**: Whisper lo necesita para el procesamiento de audio.
    -   **En Debian/Ubuntu**:
        ```bash
        sudo apt update && sudo apt install ffmpeg
        ```
    -   **En macOS (usando Homebrew)**:
        ```bash
        brew install ffmpeg
        ```
    -   **En Windows**:
        Descarga el ejecutable desde el [sitio oficial de FFmpeg](https://ffmpeg.org/download.html) y añade la ruta a su carpeta `bin` a la variable de entorno `PATH` del sistema.

## Configuración del Proyecto

Sigue estos pasos para poner en marcha el servidor:

1.  **Clonar el repositorio (o crear los archivos)**
    Si tienes esto en un repositorio git:
    ```bash
    git clone <url-del-repositorio>
    cd transcription-api
    ```
    Si no, crea la carpeta `transcription-api` y los archivos `main.py`, `requirements.txt` y `.env.example` como se describe en esta guía.

2.  **Crear un entorno virtual**
    Es una buena práctica para aislar las dependencias del proyecto.
    ```bash
    python -m venv venv
    ```
    **Activar el entorno virtual:**
    -   En Linux/macOS: `source venv/bin/activate`
    -   En Windows: `.\venv\Scripts\activate`

3.  **Instalar las dependencias**
    ```bash
    pip install -r requirements.txt
    ```
    *Nota: La primera vez que se ejecute el servidor, se descargará el modelo de Whisper (`base`), lo que puede tardar unos minutos y requiere conexión a internet.*

4.  **Configurar el token de seguridad**
    Copia el archivo de ejemplo `.env.example` a un nuevo archivo llamado `.env`.
    ```bash
    cp .env.example .env
    ```
    Abre el archivo `.env` y reemplaza `"CAMBIA_ESTE_TOKEN_SECRETO"` por un token seguro de tu elección. Por ejemplo: `API_TOKEN="my-super-secret-and-long-api-token"`.

## Ejecutar la Aplicación

Con el entorno virtual activado, ejecuta el siguiente comando en la terminal:

```bash
uvicorn main:app --reload
```

-   `uvicorn`: Es el servidor ASGI que ejecuta la aplicación.
-   `main:app`: Le dice a `uvicorn` que busque el objeto `app` en el archivo `main.py`.
-   `--reload`: Reinicia el servidor automáticamente cada vez que se detectan cambios en el código.

La API estará disponible en `http://127.0.0.1:8000`.

## Cómo Usar la API

Para interactuar con los endpoints, necesitas incluir tu token en la cabecera de autorización.

**Cabecera de Autorización:** `Authorization: Bearer TU_TOKEN_SECRETO`

### API 1: Transcribir Archivo (`/upload-file-transcribe`)

-   **Método**: `POST`
-   **Descripción**: Sube un archivo de audio o video.
-   **Ejemplo con `curl`**:
    ```bash
    curl -X POST "http://127.0.0.1:8000/upload-file-transcribe" \
    -H "Authorization: Bearer TU_TOKEN_SECRETO" \
    -F "file=@/ruta/a/tu/archivo.mp3"
    ```

-   **Respuesta Exitosa (JSON)**:
    ```json
    {
      "transcription": "El texto del audio transcrito aparecerá aquí."
    }
    ```

### API 2: Transcribir URL de YouTube (`/youtube-url-transcribe`)

-   **Método**: `POST`
-   **Descripción**: Envía una URL de YouTube en un cuerpo JSON.
-   **Ejemplo con `curl`**:
    ```bash
    curl -X POST "http://127.0.0.1:8000/youtube-url-transcribe" \
    -H "Authorization: Bearer TU_TOKEN_SECRETO" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
    ```

-   **Respuesta Exitosa (JSON)**:
    ```json
    {
      "transcription": "Never gonna give you up, never gonna let you down..."
    }
    ```

### Documentación Interactiva

Una vez que el servidor esté en funcionamiento, puedes explorar y probar la API de forma interactiva visitando las siguientes URLs en tu navegador:

-   **Swagger UI**: `http://127.0.0.1:8000/docs`
-   **ReDoc**: `http://127.0.0.1:8000/redoc`

Desde estas interfaces puedes probar los endpoints, y Swagger UI gestionará automáticamente el token de autorización por ti si haces clic en el botón "Authorize".

