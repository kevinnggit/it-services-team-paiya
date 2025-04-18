def validate_free_prompt(data):
    if not isinstance(data.get("data"), str) or not data.get("data").strip():
        return False, "Antworttext fehlt oder ist ungültig."
    return True, "Valid free prompt response"

def validate_summary(data):
    if not isinstance(data.get("summary"), str) or not data.get("summary").strip():
        return False, "Zusammenfassung fehlt oder ist ungültig."
    return True, "Valid summary response"

def validate_fun_fact(data):
    if not isinstance(data.get("fact"), str) or not data.get("fact").strip():
        return False, "Fun Fact fehlt oder ist ungültig."
    if not isinstance(data.get("source"), str) or not data.get("source").strip():
        return False, "Quellenangabe fehlt oder ist ungültig."
    return True, "Valid fun fact response"

def validate_quiz(data):
    if not isinstance(data.get("question"), str) or not data["question"].strip():
        return False, "Quizfrage fehlt oder ist ungültig."
    if not isinstance(data.get("options"), list) or len(data["options"]) < 2:
        return False, "Antwortmöglichkeiten fehlen oder sind ungültig."
    if not isinstance(data.get("answer"), str) or not data["answer"].strip():
        return False, "Korrekte Antwort fehlt oder ist ungültig."
    return True, "Valid quiz response"

def validate_response(route_type, data):
    validators = {
        "FreePrompt": validate_free_prompt,
        "Summary": validate_summary,
        "FunFact": validate_fun_fact,
        "Quiz": validate_quiz
    }

    validator = validators.get(route_type)
    if not validator:
        return False, f"Keine Validierung für Typ: {route_type}"

    return validator(data)