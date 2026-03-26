import cv2  # OpenCV für die Bildaufnahme von der Webcam
import base64  # Zum Umwandeln des Bildes in ein Textformat für die API
import os  # Zum Löschen der temporären Bilddatei
import time  # Für kleine Pausen (z. B. Kamera-Fokus)
from gpiozero import Button  # Steuerung des physischen Tasters am Raspberry Pi
from signal import pause  # Hält das Skript aktiv, damit es auf Events warten kann
from openai import OpenAI  # Schnittstelle zur OpenAI KI

# --- 1. Konfiguration ---
# Erstellt den Client für die API-Kommunikation
client = OpenAI(api_key="DEIN-API-KEY")

# Definiert den GPIO-Pin, an dem dein Taster angeschlossen ist (hier Pin 2)
button = Button(2)

# Name der Zwischenspeicher-Datei für das Foto
temp_file = "auswertung.jpg"


def encode_image(image_path):
    """
    Wandelt ein lokales Bild in einen Base64-String um.
    KI-Modelle können keine rohen Dateien empfangen, sondern benötigen dieses Format.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def analyze_waste(image_path):
    """
    Sendet das Bild an GPT-4o und stellt die spezifische Frage zum Müll.
    """
    print("Sende Bild an KI...")
    base64_image = encode_image(image_path)

    try:
        # Erstellt den API-Call mit Text-Prompt und Bild-Daten
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Was ist das für Müll? Wie lange dauert der Abbau?"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                }
            ],
        )
        # Gibt die Text-Antwort der KI zurück
        return response.choices[0].message.content
    except Exception as e:
        return f"Fehler bei der API-Anfrage: {e}"


def starte_analyse():
    """
    Hauptfunktion: Wird aufgerufen, wenn der Knopf gedrückt wird.
    Steuert Kamera -> Speicherung -> KI -> Bereinigung.
    """
    print("\n--- Taster gedrückt: Starte Analyse ---")

    # Initialisiert die Webcam (0 ist meist die Standard-Kamera)
    cam = cv2.VideoCapture(0)

    # Puffer-Zeit: Gibt der Kamera Zeit, Belichtung und Fokus anzupassen
    time.sleep(1)

    # Macht das eigentliche Foto (ret = Erfolg/Misserfolg, frame = das Bild)
    ret, frame = cam.read()

    if ret:
        # Speichert das Bild lokal auf der Festplatte/SD-Karte
        cv2.imwrite(temp_file, frame)
        # Kamera-Ressource sofort schließen, damit andere Programme darauf zugreifen könnten
        cam.release()

        # Ruft die KI-Funktion auf und gibt das Ergebnis in der Konsole aus
        ergebnis = analyze_waste(temp_file)
        print("ERGEBNIS:", ergebnis)

        # Löscht das temporäre Bild, um keinen Datenmüll zu hinterlassen
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print("Temp-Datei gelöscht.")
    else:
        print("Fehler: Kamera konnte kein Bild aufnehmen.")
        cam.release()


# --- Event-Handling ---
# Verknüpft das physische Drücken des Buttons mit der Funktion 'starte_analyse'
# Dies geschieht asynchron im Hintergrund.
button.when_pressed = starte_analyse

print("Programm bereit. Bitte Taster drücken...")

# Verhindert, dass das Python-Skript sich sofort beendet.
# Das Programm wartet hier unendlich lange auf Signale (wie den Tastendruck).
pause()