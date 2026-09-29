# Projektüberblick

## Einleitung
Dieses Repository stellt **HBVGPT** bereit, einen Chat-Assistenten, der mit großen Sprachmodellen (LLMs) arbeitet. Das System kombiniert ein Vue-Frontend und ein FastAPI-Backend. Docker sorgt für eine einheitliche Umgebung.

## Ordnerstruktur
```
.
├── Dockerfile.fastapi        # Backend Containerbau
├── docker-compose.yml        # Startet Front- und Backend
├── main.py                   # FastAPI Einstiegspunkt
├── src/                      # Backend-Logik
│   ├── chains.py             # Prompt-Logik und LLM-Aufrufe
│   └── validators.py         # Antwortvalidierungen
├── chat/                     # Frontend (Vite/Vue)
│   ├── Dockerfile            # Frontend Containerbau
│   ├── src/                  # Vue-Komponenten
│   └── vite.config.js        # Vite-Konfiguration
└── requirements.txt          # Python-Abhängigkeiten
```

## Ablauf der Anwendung
1. Der Benutzer öffnet das Frontend und wählt einen Anwendungsfall (Summary, Quiz, FreePrompt, FunFact).
2. Das Frontend sendet die Eingabe an `/api/process_query` im Backend.
3. `main.py` nimmt die Daten entgegen, wählt je nach Provider und Modell ein LLM aus und ruft die passenden Funktionen in `chains.py` auf.
4. `chains.py` verarbeitet die Anfrage: Prompt-Vorlagen werden mit LangChain erstellt, das Modell wird über Groq oder OpenAI angesprochen.
5. Die Antwort wird validiert (`validators.py`) und an das Frontend zurückgegeben.
6. Der Nutzer kann Antworten bewerten; Feedback wird über `/api/store_feedback` angenommen.

## Technologieübersicht
### FastAPI
- **Nutzen**: Schnelles Python-Webframework; stellt REST-Endpunkte bereit.
- **Rolle im Projekt**: Kern des Backends. Endpunkte verarbeiten Benutzeranfragen, rufen LLMs auf und liefern Ergebnisse.
- **Grenzen**: Kein asynchrones Laden von Modellen, abhängig von externen APIs. Skalierung erfolgt über Docker, aber keine interne Lastverteilung.

### LangChain
- **Nutzen**: Bibliothek zum Erstellen von LLM-Ketten und Prompt-Templates.
- **Rolle im Projekt**: Kapselt Prompts, Parser und LLM-Aufrufe. Sorgt für modulare Ketten (Summary, Quiz, usw.).
- **Grenzen**: Abhängig von korrekten Parsern; kann bei unerwarteten Antworten ausfallen.

### Groq & OpenAI APIs
- **Nutzen**: Externe LLM-Anbieter.
- **Rolle im Projekt**: Groq wird bevorzugt; OpenAI als Alternative. `get_llm` wählt das passende Modell.
- **Grenzen**: Kosten, Rate-Limits und Datenschutz. Antwortqualität hängt vom Modell ab.

### Vue 3 & Vite
- **Nutzen**: Moderne Frontend-Technologien für interaktive Benutzeroberflächen.
- **Rolle im Projekt**: Stellt die Chatoberfläche bereit, verwaltet State und kommuniziert mit dem Backend.
- **Grenzen**: Kein Server-Side-Rendering, rein clientseitig. Bei langsamen Verbindungen können Ladezeiten entstehen.

### Docker & Docker Compose
- **Nutzen**: Containerisierung für reproduzierbare Umgebungen.
- **Rolle im Projekt**: `docker-compose` startet Front- und Backend in isolierten Containern.
- **Grenzen**: Standard-Setup ohne Skalierung oder Orchestrierung (kein Kubernetes).

### Prometheus (Monitoring)
- **Nutzen**: Über `prometheus.yml` vorbereitet, um Metriken des Backends zu erfassen.
- **Rolle im Projekt**: Noch minimal; könnte erweitert werden, um Nutzung und Fehler zu überwachen.
- **Grenzen**: Keine vollständige Integration, daher geringe Einblicke in Performance.

## Backend im Detail
### main.py
- Erstellt ein FastAPI-Objekt und aktiviert CORS.
- `/api/process_query` verarbeitet eingehende Anfragen.
  - Liest `query`, `use_case`, `provider`, `model` und `messages` aus dem JSON-Body.
  - Ruft `get_llm` aus `chains.py` auf, um das passende LLM zu erhalten.
  - Je nach Use Case wird die zugehörige Funktion aufgerufen (`get_free_prompt_groq`, `get_summary_groq`, ...).
  - Die Antwort wird validiert und als JSON zurückgegeben.
- `/api/store_feedback` speichert Nutzerrückmeldungen; im Beispiel wird lediglich ein JSONResponse zurückgegeben.

### chains.py
- Definiert Hilfsfunktionen, Prompt-Templates und die Kernlogik für die Use Cases.
- `clean_json_output` bereinigt Modellantworten, um gültiges JSON zu extrahieren.
- `validate_input` filtert problematische Befehle (z.B. `ignore`, `system`).
- `get_llm` wählt das Modell: Für Groq wird ein spezieller Client zurückgegeben, sonst ein OpenAI-Modell über LangChain.
- Prompt-Vorlagen (Summary, Quiz, FunFact, FreePrompt) erzeugen die Texte für die LLMs.
- `call_groq` ruft die Groq-API direkt auf und liefert den Text.
- Spezifische Funktionen (`get_quiz_groq`, `get_fun_fact_groq`, ...) bereiten die Prompts vor, rufen `call_groq` und parsen JSON.
- `main` am Ende von chains.py ist eine alternative Einstiegsmethode (wird in main.py jedoch nicht direkt verwendet).

### validators.py
- Prüft die Rückgaben der Use Cases.
- Bei Ungültigkeit wird eine Fehlermeldung geliefert.

## Frontend im Detail
### chat/src/App.vue
- Enthält die komplette UI-Logik: Sidebar mit Use-Case-Auswahl, Hauptbereich für Chat und Quiz.
- Modelle und Provider lassen sich auswählen; die Auswahl wird im State gehalten.
- `sendQuery` ruft das Backend auf und verarbeitet die Antwort je nach Use Case (Chat, Zusammenfassung, Quiz, Fun Fact).
- Quizfragen werden in einer eigenen Box angezeigt; die Antwortprüfung erfolgt lokal.
- Bewertungsbuttons (“👍/👎”) ermöglichen Feedback, das an `/api/store_feedback` gesendet wird.
- Markdown wird mit `marked` gerendert und per `DOMPurify` bereinigt.
- Das Stylesheet im `<style>`-Block definiert Layout, Farbschema und responsive Verhalten.

### weitere Frontend-Dateien
- `main.js` mountet die Vue-App.
- `vite.config.js` legt Serveroptionen fest und bindet das Vue-Plugin ein.
- `index.html` enthält lediglich den Einstiegspunkt `<div id="app"></div>` und bindet die generierte JavaScript-Datei ein.

## Startanleitung
1. **Voraussetzungen**
   - Installiere [Docker](https://www.docker.com) inkl. Docker Compose.
   - Erstelle aus `.env.example` eine lokale `.env` und trage eigene API-Schlüssel ein:
     ```bash
     cp .env.example .env
     ```
     ```
     OPENAI_API_KEY=sk-...
     GROQ_API_KEY=...
     ```
2. **Container bauen und starten**
   ```bash
   docker-compose up --build
   ```
   - Frontend: http://localhost:3033
   - Backend: http://localhost:8033/api/process_query

3. **Entwicklung ohne Docker** (optional)
   - Backend: Python 3.11 installieren, `pip install -r requirements.txt` und `uvicorn main:app --reload`
   - Frontend: `cd chat && npm install && npm run dev`

## Schwachstellen
- Fehlende Tests: Es gibt keine automatisierten Tests für Backend oder Frontend.
- Sicherheit: Nur rudimentäre Eingabevalidierung; keine Authentifizierung.
- Fehlerbehandlung: Bei API-Ausfällen gibt es nur generische Fehlermeldungen.
- Feedback-Speicherung: Momentan nur ein Print-Statement – keine Persistenz.
- Keine Rate-Limits oder Nutzerverwaltung.

## Mögliche Verbesserungen
- **Tests einführen**: Unit- und Integrationstests für `chains.py` und das Vue-Frontend.
- **Persistentes Feedback**: Antworten in einer Datenbank speichern (z.B. PostgreSQL oder MongoDB).
- **Erweiterte Sicherheit**: Authentifizierung und Zugriffskontrolle, bessere Input-Sanitization.
- **Skalierung**: Einsatz eines Reverse Proxys (z.B. Nginx) und horizontaler Skalierung über Docker Swarm oder Kubernetes.
- **Monitoring ausbauen**: Prometheus vollständig integrieren, z.B. mit Alerting.
- **Caching**: Ergebnisse häufiger Anfragen zwischenspeichern, um Kosten zu reduzieren.
- **Mehr Provider**: Neben Groq und OpenAI weitere LLM-Anbieter einbinden.

## Fazit
HBVGPT demonstriert ein schlankes Zusammenspiel von Vue-Frontend und FastAPI-Backend, um verschiedene LLM-Funktionen anzubieten. Mit Docker lässt sich die Anwendung leicht lokal starten. Durch gezielte Erweiterungen – insbesondere Tests, Sicherheit und persistentes Feedback – kann das Projekt robuster und professioneller werden.

## Funktionen in chains.py im Überblick
1. **clean_json_output(text)** – Sucht nach JSON in einer Modellantwort und entfernt unnötige Umrandungen wie ```json``` oder einfache Anführungszeichen.
2. **validate_input(user_input)** – Blockiert verdächtige Schlagwörter ("ignore", "system" usw.), um Missbrauch zu verhindern.
3. **get_llm(provider, model, temperature)** – Liefert entweder einen Groq-Client mit Modellnamen oder ein OpenAI-Modellobjekt für LangChain.
4. **call_groq(prompt, client, model, temperature)** – Baut einen Request-Body, setzt ggf. "reasoning_format" und ruft die Groq-API direkt auf.
5. **get_free_prompt_groq(question, client, model, temperature)** – Sendet einen einfachen Prompt an Groq und gibt den Text zurück.
6. **get_summary_groq(text, length, client, model, temperature)** – Formatiert den Prompt für Zusammenfassungen und parst die JSON-Antwort.
7. **get_quiz_groq(topic, client, model, temperature, messages)** – Baut aus dem bisherigen Chatverlauf einen Prompt und erzeugt Quizfragen im JSON-Format.
8. **get_fun_fact_groq(word, client, model, temperature)** – Fordert einen interessanten Fakt an und prüft die Quelle.
9. **safe_invoke(chain, inputs)** – Wrapper, der Parsing-Fehler protokolliert und optional einen Fallback nutzt.
10. **main(user_query, use_case, extra_params, provider)** – Variante für direkten Aufruf; führt je nach Use Case die obigen Funktionen aus.

## Funktionen in main.py im Überblick
1. Beim Start wird eine FastAPI-App erzeugt und CORS aktiviert, damit das Frontend im Browser zugreifen kann.
2. `process_query`:
   - Erwartet JSON mit den Feldern `query`, `use_case`, `provider`, `model`, `length` und `messages`.
   - Holt sich das LLM über `get_llm`.
   - Unterscheidet zwischen Groq (direkter API-Call) und OpenAI (LangChain-Kette).
   - Nutzt je nach Use Case die richtigen Parser (`JsonOutputParser` oder `StrOutputParser`).
   - Sendet die Antwort als JSON zurück.
3. `store_feedback`:
   - Nimmt `thumbs`, `message_index`, `model`, `provider` und optionalen Freitext entgegen.
   - Druckt die Daten als JSON – hier könnte eine echte Datenbank angebunden werden.

## Weitere Dateien
- **Dockerfile.fastapi** – Mehrstufiger Build: Erst Installation der Abhängigkeiten, danach Kopie des Codes in ein schlankes Image.
- **chat/Dockerfile** – Baut das Frontend mit Node 18 und startet `npm run dev` im Container.
- **watch.sh** – Überwacht Quellcode-Änderungen und baut/pusht automatisch Docker-Images. Nützlich für CI/CD.
- **prometheus.yml** – Minimale Konfiguration, um die Metriken des Backends im Docker-Netzwerk `app-net` abzufragen.
- **requirements.txt** – Listet FastAPI, LangChain und weitere Pakete auf, die für die Backend-Logik notwendig sind.

## Erweiterte Hinweise zum Ablauf
- Der Frontend-Code speichert die letzten zehn Chatnachrichten und sendet sie bei einer neuen Anfrage mit, damit der Kontext erhalten bleibt.
- Quizfragen werden im Chatverlauf als versteckte Textnachrichten gespeichert, damit das Modell im nächsten Schritt weiß, welche Frage gestellt wurde und welche Antwort korrekt war.
- Das Frontend begrenzt die Eingabe für Zusammenfassungen über ein Dropdown (`kurz`, `mittel`, `lang`), was im Backend direkt in den Prompt einfließt.
- Beim Senden von Feedback werden neben der Bewertung auch Modellname und Provider übertragen. So ließe sich später analysieren, welches Modell bessere Antworten liefert.

## Grenzen der aktuellen Implementierung
- Die LLM-Antworten werden nicht gecachet. Bei mehrfachen identischen Fragen entstehen erneut API-Kosten.
- Die JSON-Parser schlagen fehl, wenn die Modelle eine Antwort außerhalb des erwarteten Formats liefern. Die Fehlerbehandlung könnte robuster sein.
- Für das Frontend wird nur der Dev-Server (`npm run dev`) verwendet; es gibt kein optimiertes Build für die Produktion im Dockerfile.
- Die `.env`-Datei wird direkt im Container genutzt. Sensible Schlüssel könnten sicherer verwaltet werden (z.B. via Docker Secrets).

## Weitere Verbesserungsideen
- **Automatisiertes Deployment**: Ein GitHub-Action-Workflow könnte Docker-Builds und Tests anstoßen.
- **User-Authentifizierung**: Registrierung und Login ermöglichen personalisierte Chatverläufe.
- **Mehrsprachigkeit**: Frontend und Prompts könnten dynamisch an andere Sprachen angepasst werden.
- **Feinere Steuerung der Modelle**: Temperatur, Top-p und maximale Token könnten im Frontend wählbar sein.
- **UI-Optimierungen**: Ladeindikatoren für längere Antworten, dunkles Farbschema, mobile Verbesserungen.
- **Datenpersistenz**: Chatverläufe und Feedback in einer Datenbank speichern, um Verlauf und Statistiken anzuzeigen.
- **Security Audits**: Regelmäßige Überprüfung von Abhängigkeiten (z.B. via Dependabot) und Penetration-Tests.

## Zusammenfassung des Workflows
1. Entwickler klonen das Repo und erstellen `.env` mit API-Schlüsseln.
2. `docker-compose up --build` startet zwei Container: `backend-llm` (FastAPI) und `frontend-llm` (Vite/Vue).
3. Im Browser unter http://localhost:3033 erscheint die Benutzeroberfläche.
4. Der Nutzer wählt einen Use Case und sendet eine Anfrage.
5. Das Backend ruft je nach Provider Groq oder OpenAI auf, bereitet die Antwort auf und sendet sie zurück.
6. Optional wird Feedback über den zweiten Endpunkt geschickt.
7. Prometheus kann das Backend überwachen, sofern es im selben Docker-Netzwerk läuft.
