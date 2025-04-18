import re
import json
import logging
from typing import List

from dotenv import load_dotenv
from groq import Groq
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_core.exceptions import OutputParserException

from src.validators import validate_response

load_dotenv()
logging.basicConfig(level=logging.INFO)

embedding = OpenAIEmbeddings()

##########################
# CLEAN JSON OUTPUT      #
##########################

def clean_json_output(text: str) -> str:
    if not isinstance(text, str):
        return text
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if match:
        return match.group().strip()
    text = re.sub(r"^```(?:json|python)?\s*", "", text.strip(), flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"```$", "", text.strip(), flags=re.MULTILINE)
    text = re.sub(r"^['\"]{1,3}|['\"]{1,3}$", "", text.strip())
    return text.strip()

##########################
# VALIDATION             #
##########################

def validate_input(user_input):
    pattern = re.compile(r"(ignore|bypass|override|forget|system|prompt)", re.IGNORECASE)
    if pattern.search(user_input):
        raise ValueError("Unsichere Eingabe erkannt. Bitte formuliere deine Frage neutral und ohne Systembefehle.")
    return user_input

##########################
# LLM FACTORY            #
##########################

def get_llm(provider=None, model=None, temperature=0.1):
    default_models = {
        "openai": "gpt-4o",
        "groq": "deepseek-r1-distill-llama-70b"
    }

    model = model or default_models.get(provider, "deepseek-r1-distill-llama-70b")

    if provider == "groq":
        return {
            "provider": "groq",
            "client": Groq(),
            "model": model,
            "temperature": temperature
        }
    else:
        return ChatOpenAI(model=model, temperature=temperature)

##########################
# LANGCHAIN USE CASES    #
##########################

free_prompt_template = PromptTemplate(
    template="Beantworte ehrlich und hilfreich: {question}",
    input_variables=["question"]
)

class SummaryInput(BaseModel):
    summary: str = Field(description="Zusammenfassung")

summary_parser = JsonOutputParser(pydantic_object=SummaryInput)

summary_prompt = PromptTemplate(
    template="""
Fasse den folgenden Text in einer {length}-Zusammenfassung zusammen. Antworte im JSON-Format:
{{ "summary": "..." }}

Text:
{text}

{format_instructions}
""",
    input_variables=["text", "length"],
    partial_variables={"format_instructions": summary_parser.get_format_instructions()}
)

class QuizResponse(BaseModel):
    question: str = Field(description="Die Quizfrage")
    options: List[str] = Field(description="Antwortmöglichkeiten")
    answer: str = Field(description="Korrekte Antwort")
    explanation: str = Field(description="Kurze Erläuterung zur richtigen Antwort")

quiz_parser = JsonOutputParser(pydantic_object=QuizResponse)

quiz_prompt = PromptTemplate(
    template="""
Erstelle nun eine neue Multiple-Choice-Quizfrage zum Thema basierend auf dem Verlauf **ohne Wiederholung**:

Beachte:
- Formuliere eine **kreative und thematisch passende Frage** mit 4 Antwortmöglichkeiten.
- **Stelle eine neue, kreative Frage, die bisher noch **nicht** inhaltlich oder wörtlich gestellt wurde**.
- Markiere die richtige Antwort exakt, wie es bei den Möglichkeiten steht z.B. 'answer': 'B) ...'
- Gib eine kurze, sachliche Erläuterung, warum diese Antwort korrekt ist (mit Quelle).
- Antworte **ausschließlich im JSON-Format** – keine zusätzlichen Erklärungen oder Texte.

Antwortformat im JSON:
{{
  "question": "...",
  "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
  "answer": "...",
  "explanation": "..."
}}

{format_instructions}
""",
    input_variables=["topic"],
    partial_variables={"format_instructions": quiz_parser.get_format_instructions()}
)


class FunFactResponse(BaseModel):
    fact: str = Field(description="Ein interessanter Fakt")
    source: str = Field(description="Quelle des Fakts")

fun_fact_parser = JsonOutputParser(pydantic_object=FunFactResponse)

fun_fact_prompt = PromptTemplate(
    template="""
Gib mir einen interessanten Fun Fact basierend auf dem Wort: {word}. 

Wähle nur verlässliche und öffentlich erreichbare Quellen. Überprüfe vor dem Bereitstellen, ob die Quelle tatsächlich erreichbar ist (z. B. durch einen erfolgreichen Zugriff oder HEAD-Request).

Antwortformat im JSON:
{{ "fact": "...", "source": "..." }}

{format_instructions}
""",
    input_variables=["word"],
    partial_variables={"format_instructions": fun_fact_parser.get_format_instructions()}
)

##########################
# GROQ DIRECT CALLS      #
##########################

REASONING_SUPPORTED_MODELS = {
    "qwen-qwq-32b",
    "deepseek-r1-distill-llama-70b",
}

def call_groq(prompt: str, client, model, temperature):
    request_body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "top_p": 0.95,
        "max_completion_tokens": 1024,
        "stream": False
    }

    if model in REASONING_SUPPORTED_MODELS:
        request_body["reasoning_format"] = "parsed"

    response = client.chat.completions.create(**request_body)
    return response.choices[0].message.content.strip()


def get_fun_fact_groq(word: str, client, model, temperature):
    prompt = f"""
Gib mir einen interessanten Fun Fact basierend auf dem Wort: {word}. 

Wähle nur verlässliche und öffentlich erreichbare Quellen. Überprüfe vor dem Bereitstellen, ob die Quelle tatsächlich erreichbar ist (z. B. durch einen erfolgreichen Zugriff oder HEAD-Request).

Antwortformat im JSON:
{{ "fact": "...", "source": "..." }}
"""
    raw = call_groq(prompt, client, model, temperature)
    cleaned = clean_json_output(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logging.error(f"Ungültige JSON-Antwort: {cleaned}")
        return {"error": "Ungültige Antwort vom Modell"}

def get_quiz_groq(topic: str, client, model, temperature, messages: list = None):
    prompt_topic = build_chat_context(messages or [], topic)
    prompt = f"""Du bist ein Quiz-Generator. Dein Ziel ist es, eine **einzigartige Multiple-Choice-Frage** zu stellen, die sich **inhaltlich klar von vorherigen Fragen unterscheidet**.

    Vorherige Fragen und Inhalte (Chatverlauf):
    {prompt_topic}

    Erstelle nun eine neue Multiple-Choice-Quizfrage zum Thema basierend auf dem Verlauf **ohne Wiederholung**:

    Beachte:
    - Stelle eine neue, kreative Frage, die bisher noch **nicht inhaltlich oder wörtlich gestellt wurde**.
    - Vermeide ähnliche Formulierungen, Inhalte oder Antwortmöglichkeiten wie im Chatverlauf.
    - Gib 4 verschiedene Antwortoptionen.
    - Markiere die korrekte Antwort exakt, z.B. 'answer': 'C) ...'
    - Gib eine kurze Erklärung mit Quelle.
    - Antworte **ausschließlich im JSON-Format**, ohne zusätzlichen Text.

    Antwortformat im JSON:
    {{
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "answer": "...",
      "explanation": "..."
    }}
    """
    raw = call_groq(prompt, client, model, temperature)
    cleaned = clean_json_output(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logging.error(f"Ungültige JSON-Antwort: {cleaned}")
        return {"error": "Ungültige Antwort vom Modell"}


def get_summary_groq(text: str, length: str, client, model, temperature):
    prompt = f"""
Fasse den folgenden Text in einer {length}-Zusammenfassung zusammen. Antworte im JSON-Format:
{{ "summary": "..." }}

Text:
{text}
"""
    raw = call_groq(prompt, client, model, temperature)
    cleaned = clean_json_output(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logging.error(f"Ungültige JSON-Antwort: {cleaned}")
        return {"error": "Ungültige Antwort vom Modell"}

def get_free_prompt_groq(question: str, client, model, temperature):
    prompt = f"Beantworte ehrlich und hilfreich: {question}"
    raw = call_groq(prompt, client, model, temperature)
    return clean_json_output(raw)

##########################
# SAFE INVOKE HELPER     #
##########################

def safe_invoke(chain, inputs, fallback=None, context=""):
    try:
        return chain.invoke(inputs)
    except OutputParserException as e:
        logging.error(f"Parsing-Fehler in {context}: {e}")
        if fallback:
            return fallback()
        raise
    except Exception as e:
        logging.error(f"Unerwarteter Fehler in {context}: {e}")
        if fallback:
            return fallback()
        raise

##########################
# MAIN LOGIC             #
##########################

def main(user_query, use_case: str, extra_params=None, provider="openai"):
    try:
        validated_query = validate_input(user_query)
        logging.info(f"Use Case gewählt: {use_case} (Provider: {provider})")

        llm = get_llm(provider=provider)

        if isinstance(llm, dict) and llm.get("provider") == "groq":
            client = llm["client"]
            model = llm["model"]
            temperature = llm["temperature"]

            if use_case == "FreePrompt":
                result = get_free_prompt_groq(validated_query, client, model, temperature)
                valid, msg = validate_response("FreePrompt", {"data": result})
                if not valid:
                    return {"error": msg}
                return {"type": "free_prompt", "data": result}

            elif use_case == "Summary":
                if not extra_params or "length" not in extra_params:
                    raise ValueError("Länge der Zusammenfassung fehlt.")
                result = get_summary_groq(validated_query, extra_params["length"], client, model, temperature)
                valid, msg = validate_response("Summary", result)
                if not valid:
                    return {"error": msg}
                return {"type": "summary", **result}

            elif use_case == "Quiz":
                result = get_quiz_groq(validated_query, client, model, temperature)
                valid, msg = validate_response("Quiz", result)
                if not valid:
                    return {"error": msg}
                return {"type": "quiz", **result}

            elif use_case == "FunFact":
                result = get_fun_fact_groq(validated_query, client, model, temperature)
                valid, msg = validate_response("FunFact", result)
                if not valid:
                    return {"error": msg}
                return {"type": "fun_fact", **result}

            else:
                return {"type": "not_supported", "message": "Diese Anfrage wird derzeit nicht unterstützt."}

        else:
            if use_case == "FreePrompt":
                chain = free_prompt_template | llm | StrOutputParser()
                result = safe_invoke(chain, {"question": validated_query}, context="FreePrompt")
                valid, msg = validate_response("FreePrompt", {"data": result})
                if not valid:
                    return {"error": msg}
                return {"type": "free_prompt", "data": result}

            elif use_case == "Summary":
                if not extra_params or "length" not in extra_params:
                    raise ValueError("Länge der Zusammenfassung fehlt.")
                chain = summary_prompt | llm | summary_parser
                result = safe_invoke(chain, {"text": validated_query, "length": extra_params["length"]}, context="Summary")
                valid, msg = validate_response("Summary", result)
                if not valid:
                    return {"error": msg}
                return {"type": "summary", **result}

            elif use_case == "Quiz":
                chain = quiz_prompt | llm | quiz_parser
                result = safe_invoke(chain, {"topic": validated_query}, context="Quiz")
                valid, msg = validate_response("Quiz", result)
                if not valid:
                    return {"error": msg}
                return {"type": "quiz", **result}

            elif use_case == "FunFact":
                chain = fun_fact_prompt | llm | fun_fact_parser
                result = safe_invoke(chain, {"word": validated_query}, context="FunFact")
                valid, msg = validate_response("FunFact", result)
                if not valid:
                    return {"error": msg}
                return {"type": "fun_fact", **result}

            else:
                return {"type": "not_supported", "message": "Diese Anfrage wird derzeit nicht unterstützt."}

    except ValueError as ve:
        logging.warning(f"Validierungsfehler: {ve}")
        return {"error": str(ve)}

def build_chat_context(messages: list, current_query: str = None) -> str:
    history = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    if current_query:
        history += f"\nuser: {current_query}"
    return history.strip()

