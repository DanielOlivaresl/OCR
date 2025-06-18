from django.shortcuts import render
from django.conf import settings
import os
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from PyPDF2 import PdfReader  # Para extraer texto de PDFs
    # import pdfplumber  # Para una extracción más precisa
from docx import Document  # Para manejar archivos .docx
import easyocr  # Para realizar OCR en imágenes
from paddleocr import PaddleOCR 
from gtts import gTTS   

from elevenlabs.client import ElevenLabs
from elevenlabs import play


def even_labs_tts(texto, archivo_salida):
    """Convierte texto a audio usando ElevenLabs y crea directorios si no existen"""
    try:
        # Verificar y crear directorios si no existen
        os.makedirs(os.path.dirname(archivo_salida), exist_ok=True)
        
        client = ElevenLabs(
            api_key="sk_155e9ab0332731c88f417366e77bd0b3b8c21d61b8b52600"
        )
        
        audio_stream = client.text_to_speech.convert(
            text=texto,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        
        # Guardar el archivo
        with open(archivo_salida, "wb") as f:
            for chunk in audio_stream:
                if chunk:
                    f.write(chunk)
        
        print(f"Audio ElevenLabs guardado en: {archivo_salida}")
        return True
    except Exception as e:
        print(f"Error en ElevenLabs TTS: {str(e)}")
        return False
def texto_a_audio(texto, archivo_salida):
        """Convierte texto a un archivo de audio MP3."""
        tts = gTTS(text=texto, lang="es", slow=False)
        tts.save(archivo_salida)
        print(f"Audio guardado en: {archivo_salida}")    


def read_image_with_paddleocr(file_path):
    """Realiza OCR en una imagen usando PaddleOCR con manejo de errores."""
    try:
        ocr = PaddleOCR(use_angle_cls=True, lang="es")
        result = ocr.ocr(file_path, cls=True)
        
        # Verificar si se encontró texto
        if not result or not result[0]:
            return None  # Retorna None si no se encontró texto
        
        # Extraer texto de cada línea encontrada
        texto_extraido = [line[1][0] for line in result[0] if line and len(line) > 1 and line[1]]
        
        # Unir todas las líneas de texto encontradas
        texto_final = " ".join(texto_extraido) if texto_extraido else None
        return texto_final
        
    except Exception as e:
        print(f"Error en OCR: {str(e)}")
        return None

def read_pdf(file_path):
        """Lee texto de un PDF usando PyPDF2."""
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text    


def read_docx(file_path):
        """Lee texto de un documento Word (.docx)."""
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text    


# Create your views here.
def bienvenida(request):
        return render(request, 'index.html')        

def cargar_archivo(request):
    """Procesa el archivo subido y genera un MP3 con el contenido."""
    if request.method == "POST" and request.FILES["file"]:
        archivo = request.FILES["file"]
        file_extension = os.path.splitext(archivo.name)[1].lower()
        # Guardar el archivo en la carpeta local
        file_path = os.path.join(settings.MEDIA_ROOT, archivo.name)
        if os.path.exists(file_path):
            os.remove(file_path)
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(archivo.name, archivo)
        file_url = os.path.join(settings.MEDIA_URL, filename)

        # Determinar el tipo de archivo
        file_type = archivo.content_type
        mensaje = None
        contenido = None

        # Procesar el archivo y extraer el contenido con manejo de errores
        try:
            if file_type == "application/pdf":
                print("El archivo subido es un PDF.")
                
                contenido = read_pdf(file_path)
                if not contenido or contenido.strip() == "":
                    mensaje = "No se encontró texto en el PDF."
            elif file_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                print("El archivo subido es un documento Word.")
                contenido = read_docx(file_path)
                if not contenido or contenido.strip() == "":
                    mensaje = "No se encontró texto en el documento Word."
            elif file_type.startswith("image/"):
                print("El archivo subido es una imagen.")
                contenido = read_image_with_paddleocr(file_path)
                if contenido is None:
                    mensaje = "No se encontró texto en la imagen."
            else:
                print("El tipo de archivo subido no está reconocido.")
                contenido = "Tipo de archivo no soportado."
                mensaje = "Tipo de archivo no soportado."
        except Exception as e:
            print(f"Error al procesar archivo: {str(e)}")
            contenido = f"Error al procesar el archivo: {str(e)}"
            mensaje = "Ocurrió un error al procesar el archivo."

        print(contenido)

        # Crear el archivo MP3 solo si hay contenido válido
        audio_url = None
        if contenido and contenido.strip() != "" and not mensaje:
            audio_path = os.path.join(settings.MEDIA_ROOT, f"{os.path.splitext(archivo.name)[0]}.mp3")
            texto_a_audio(contenido, audio_path)
            # even_labs_tts(contenido,audio_path)
            audio_url = os.path.join(settings.MEDIA_URL, f"{os.path.splitext(archivo.name)[0]}.mp3")
        elif not mensaje:
            mensaje = "No se encontró texto en el documento."

        # Renderizar la página con las URLs del archivo y audio
        return render(request, "leer.html", {
            "file_url": file_url,
            "contenido": contenido,
            "audio_url": audio_url,
            "mensaje": mensaje,
            "file_extension": file_extension  # Añade esto
        })

    return render(request, "index.html")

def subir_foto(request):
    """Procesa la foto subida, realiza OCR y genera un MP3 del texto extraído."""
    if request.method == 'POST' and 'photo' in request.FILES:
        photo = request.FILES['photo']
        save_path = os.path.join(settings.MEDIA_ROOT, 'fotos', photo.name)

        # Guarda la foto en la carpeta media/fotos
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'fotos'), exist_ok=True)
        with open(save_path, 'wb+') as destination:
            for chunk in photo.chunks():
                destination.write(chunk)

        # Realizar OCR en la foto con manejo de errores
        contenido = read_image_with_paddleocr(save_path)
        
        # Determinar mensajes según el resultado del OCR
        if contenido is None:
            mensaje = "No se encontró texto en la imagen."
            audio_url = None
        else:
            mensaje = "¡Texto encontrado en la imagen!"
            print(f"Texto extraído de la foto: {contenido}")
            
            # Crear el archivo MP3 del texto extraído
            audio_path = os.path.join(settings.MEDIA_ROOT, 'fotos', f"{os.path.splitext(photo.name)[0]}.mp3")
            texto_a_audio(contenido, audio_path)
            
            audio_url = f"{settings.MEDIA_URL}fotos/{os.path.splitext(photo.name)[0]}.mp3"

        # Generar URL para la foto
        photo_url = f"{settings.MEDIA_URL}fotos/{photo.name}"

        return render(request, 'foto.html', {
            'photo_url': photo_url,
            'audio_url': audio_url,
            'contenido': contenido,
            'mensaje': mensaje
        })

    elif request.method == 'GET':
        # Buscar el archivo de imagen más reciente
        folder_path = os.path.join(settings.MEDIA_ROOT, 'fotos')
        if os.path.exists(folder_path):
            image_files = sorted(
                [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))],
                key=lambda x: os.path.getmtime(os.path.join(folder_path, x)),
                reverse=True
            )
            audio_files = sorted(
                [f for f in os.listdir(folder_path) if f.endswith('.mp3')],
                key=lambda x: os.path.getmtime(os.path.join(folder_path, x)),
                reverse=True
            )

            photo_url = f"{settings.MEDIA_URL}fotos/{image_files[0]}" if image_files else None
            audio_url = f"{settings.MEDIA_URL}fotos/{audio_files[0]}" if audio_files else None
            
            # Determinar mensaje para GET request
            if photo_url and not audio_url:
                mensaje = "No se encontró texto en la imagen anterior."
            elif photo_url and audio_url:
                mensaje = "Resultados de la última imagen procesada:"
            else:
                mensaje = "No se ha subido ninguna foto aún."
        else:
            photo_url = None
            audio_url = None
            mensaje = "No se ha subido ninguna foto aún."

        return render(request, 'foto.html', {
            'photo_url': photo_url,
            'audio_url': audio_url,
            'contenido': None,
            'mensaje': mensaje
        })