import os
import shutil
import tempfile
from typing import Annotated

import whisper
import yt_dlp
from dotenv import load_dotenv
from fastapi import (FastAPI, File, HTTPException, UploadFile, Depends)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
import logging

# --- Configuración Inicial ---

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Inicializar la aplicación FastAPI
app = FastAPI(
    title="API de Transcripción de Audio/Video",
    description=(
        "Procesa archivos y URLs de YouTube para transcribir su "
        "contenido a texto."
    ),
    version="1.0.1"
)

# Cargar el modelo de Whisper.
# Se recomienda 'base' para un buen equilibrio entre rendimiento y precisión.
# Otros modelos disponibles: 'tiny', 'small', 'medium', 'large'.
# El modelo se carga una sola vez al iniciar la aplicación para mayor
# eficiencia.
print("Cargando el modelo de Whisper...")
try:
    model = whisper.load_model("base")
    print("Modelo de Whisper cargado exitosamente.")
except Exception as e:
    print(f"Error al cargar el modelo de Whisper: {e}")
    # Si el modelo no se puede cargar, la aplicación no puede funcionar.
    # Podríamos decidir salir o manejarlo de otra forma.
    exit()


# --- Seguridad: Autenticación con Token Bearer ---
# Esquema de seguridad para el token Bearer
security = HTTPBearer()

# Obtener el token de la variable de entorno
API_TOKEN = os.getenv("API_TOKEN")

if not API_TOKEN:
    raise ValueError(
        "La variable de entorno API_TOKEN no está configurada. "
        "Por favor, créala en el archivo .env."
    )

# Función de dependencia para validar el token
  
def get_current_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
):
    """
    Valida el token Bearer proporcionado en la cabecera Authorization.
    """
    if (
        not credentials or credentials.scheme != "Bearer" or
        credentials.credentials != API_TOKEN
    ):
        raise HTTPException(
            status_code=403,
            detail="Token inválido o ausente."
        )
    return credentials.credentials

# --- Modelos de Datos (Pydantic) ---


class TranscriptionResponse(BaseModel):
    """Modelo de respuesta para las transcripciones."""
    transcription: str

 
class YouTubeURLRequest(BaseModel):
    """Modelo de solicitud para la URL de YouTube."""
    url: str

  
class PingResponse(BaseModel):
    """Modelo de respuesta para el endpoint de ping."""
    status: str
    message: str

# --- Lógica de Transcripción ---

  
def transcribe_audio_file(file_path: str) -> str:
    """
    Función auxiliar para transcribir un archivo de audio usando Whisper.
    
    Args:
        file_path: La ruta al archivo de audio/video.
        
    Returns:
        El texto transcrito.
    """
    try:
        result = model.transcribe(file_path, fp16=False)
        return result["text"]
    except Exception as e:
        # Captura errores específicos de Whisper si es necesario
        raise HTTPException(
            status_code=500,
            detail=f"Error durante la transcripción: {str(e)}"
        )


# --- Endpoints de la API ---

@app.get(
    "/ping",
    response_model=PingResponse,
    summary="Verificar el estado del servicio",
    tags=["Health Check"]
)
async def ping():
    """
    Endpoint público para verificar que la API está activa y funcionando.
    No requiere autenticación.
    """
    # Se verifica implícitamente que el modelo de Whisper esté cargado,
    # ya que si falla la carga, la app no se inicia.
    return {"status": "success", "message": "API is active and running"}

  
@app.post(
    "/upload-file-transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribir un archivo de audio/video",
    dependencies=[Depends(get_current_token)],
    tags=["Transcription"]
)
async def upload_file_transcribe(
    file: Annotated[
        UploadFile,
        File(description="Archivo de audio o video a transcribir.")
    ]
):
    """
    Sube un archivo multimedia, extrae el audio y lo transcribe a texto.
    
    - **Autenticación**: Requiere un Token Bearer.
    - **Archivo**: Acepta formatos de audio y video compatibles con ffmpeg.
    """
    print(f"Recibiendo archivo: {file.filename}")
    # Crear un archivo temporal para guardar el contenido subido
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[1]
    ) as tmp_file:
        print(f"Guardando archivo temporal en: {tmp_file.name}")
        # Guardar el contenido del archivo subido en el archivo temporal
        shutil.copyfileobj(file.file, tmp_file)
        tmp_file_path = tmp_file.name

    try:
        print(f"Iniciando transcripción del archivo: {tmp_file_path}")
        # Realizar la transcripción
        transcribed_text = transcribe_audio_file(tmp_file_path)
        print("Transcripción completada exitosamente.")
    except Exception as e:
        print(f"Error durante la transcripción: {e}")
        raise
    finally:
        # Asegurarse de que el archivo temporal se elimine después de su uso
        print(f"Eliminando archivo temporal: {tmp_file_path}")
        os.unlink(tmp_file_path)
        
    return {"transcription": transcribed_text}


@app.post(
    "/youtube-url-transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribir audio de una URL de YouTube",
    dependencies=[Depends(get_current_token)],
    tags=["Transcription"]
)
async def youtube_url_transcribe(request: YouTubeURLRequest):
    """
    Descarga el audio de un video de YouTube, lo transcribe y
    devuelve el texto.

    - **Autenticación**: Requiere un Token Bearer.
    - **URL**: La URL completa del video de YouTube.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("yt_transcribe")

    logger.info(f"Recibida URL de YouTube: {request.url}")

    # Leer la ruta de cookies desde la variable de entorno (opcional)
    YT_COOKIES_PATH = os.getenv("YT_COOKIES_PATH")
    if YT_COOKIES_PATH and not os.path.exists(YT_COOKIES_PATH):
        logger.warning(f"El archivo de cookies especificado no existe: {YT_COOKIES_PATH}")
        YT_COOKIES_PATH = None

    # Crear un directorio temporal para la descarga
    temp_dir = tempfile.mkdtemp()
    logger.info(f"Directorio temporal creado: {temp_dir}")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'noplaylist': True,
    }
    if YT_COOKIES_PATH:
        ydl_opts['cookiesfrombrowser'] = ('chrome',)  # fallback if path not set
        ydl_opts['cookiefile'] = YT_COOKIES_PATH
        logger.info(f"Usando cookies de: {YT_COOKIES_PATH}")

    try:
        logger.info("Iniciando descarga de audio con yt-dlp...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(request.url, download=True)
            downloaded_file_path = ydl.prepare_filename(info_dict).replace(
                os.path.splitext(ydl.prepare_filename(info_dict))[1], ".mp3"
            )
        logger.info(f"Archivo descargado: {downloaded_file_path}")

        if not os.path.exists(downloaded_file_path):
            logger.error("No se encontró el archivo descargado.")
            raise HTTPException(
                status_code=500,
                detail=(
                    "No se pudo descargar o encontrar el archivo de audio de YouTube."
                )
            )

        logger.info("Iniciando transcripción del archivo descargado...")
        transcribed_text = transcribe_audio_file(downloaded_file_path)
        logger.info("Transcripción completada exitosamente.")

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Error al descargar el video de YouTube: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=(
                "Error al descargar el video de YouTube. "
                "Es posible que se requiera autenticación/cookies. "
                "Consulta la documentación: "
                "https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp"
            )
        )
    except Exception as e:
        logger.error(f"Ocurrió un error inesperado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ocurrió un error inesperado: {str(e)}"
        )
    finally:
        # Limpiar el directorio temporal y su contenido
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Directorio temporal eliminado: {temp_dir}")

    return {"transcription": transcribed_text}

  
@app.get("/", summary="Endpoint de Bienvenida", include_in_schema=False)
def read_root():
    return {
        "message": (
            "Bienvenido a la API de Transcripción. "
            "Visita /docs para ver la documentación."
        )
    }
