import cv2  # OpenCV für die Bildaufnahme von der Webcam
import base64  # Zum Umwandeln des Bildes in ein Textformat für die API
import os  # Zum Löschen der temporären Bilddatei
import time  # Für kleine Pausen (z. B. Kamera-Fokus)
from gpiozero import Button  # Steuerung des physischen Tasters am Raspberry Pi
from signal import pause  # Hält das Skript aktiv, damit es auf Events warten kann
from openai import OpenAI  # Schnittstelle zur OpenAI KI

# --- 1. Konfiguration ---
client = OpenAI(api_key="DEIN-API-KEY")
button = Button(2)
temp_file = "auswertung.jpg"


def encode_image(image_path):
    """
    Wandelt ein lokales Bild in einen Base64-String um.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def analyze_waste(image_path):
    """
    Sendet das Bild an GPT-4o und bittet um eine einfache Text-Antwort.
    """
    print("Sende Bild an KI...")
    base64_image = encode_image(image_path)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein Experte für Umwelttechnik und Abfallwirtschaft. Deine Antworten sind präzise, faktenbasiert und motivierend. Du antwortest immer in einer klaren, leicht lesbaren Text-Struktur."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analysiere das beigefügte Bild dieses Mülleimers. Identifiziere den markantesten Gegenstand, der weggeworfen wurde.\n\nBitte antworte übersichtlich formatiert:\n\nGegenstand: [Name]\nAbbauzeit: [Dauer bis zum Abbau in der Natur]\nVermeidung: [1-2 konkrete Tipps]"
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        },
                    ],
                }
            ],
        )
        # Gibt einfach den reinen Text zurück
        return response.choices[0].message.content
    except Exception as e:
        return f"Fehler bei der API-Anfrage: {e}"


def starte_analyse():
    """
    Hauptfunktion: Wird aufgerufen, wenn der Knopf gedrückt wird.
    """
    print("\n--- Taster gedrückt: Starte Analyse ---")

    cam = cv2.VideoCapture(0)
    time.sleep(1)
    ret, frame = cam.read()

    if ret:
        cv2.imwrite(temp_file, frame)
        cam.release()

        # Holt sich den einfachen Text von der KI
        ergebnis = analyze_waste(temp_file)

        # Gibt den Text 1:1 in der Konsole aus
        print("\n=== ERGEBNIS DER ANALYSE ===")
        print(ergebnis)
        print("============================\n")

        if os.path.exists(temp_file):
            os.remove(temp_file)
            print("Temp-Datei gelöscht.")
    else:
        print("Fehler: Kamera konnte kein Bild aufnehmen.")
        cam.release()


# --- Event-Handling ---
button.when_pressed = starte_analyse

print("Programm bereit. Bitte Taster drücken...")
pause()