HBVGPT PROJECT OVERVIEW
=======================

1. Purpose
----------
This repository contains "HBVGPT", an AI-powered assistant designed
for daily work tasks. The code base provides a FastAPI backend and a
Vue 3 frontend packaged through Docker. It supports summarization,
quiz generation, open prompts and fun facts via different large
language model providers.

2. Directory Structure
----------------------
- `main.py` – FastAPI application with two endpoints. Handles user
  prompts and feedback storage.
- `src/` – Helper modules used by the backend.
  - `chains.py` – Contains prompt templates, LLM integrations and
    helper functions.
  - `validators.py` – Validates responses from LLMs based on use case.
- `chat/` – Vue frontend built with Vite. Contains components and style
  for the chat UI.
- `Dockerfile.fastapi` – Build instructions for the backend container.
- `chat/Dockerfile` – Build instructions for the frontend container.
- `docker-compose.yml` – Starts both services together.
- `requirements.txt` – Python dependencies.
- `watch.sh` – Utility to watch for changes and rebuild Docker images.

3. Technology Flow
------------------
1. **Frontend (Vue)** collects user input and displays responses.
2. The Vue code sends a POST request to `/api/process_query` on the
   backend.
3. **FastAPI** receives the request and calls `get_llm()` from
   `src/chains.py` to obtain an LLM client depending on the chosen
   provider.
4. Based on the selected use case, the backend invokes templates or
   direct Groq calls to produce a summary, quiz, free prompt answer or
   fun fact.
5. After processing, results are validated via `src/validators.py` and
   returned as JSON.
6. The frontend displays the output and optionally stores feedback via
   `/api/store_feedback`.

4. Backend in Detail
--------------------
### main.py
The FastAPI app initializes CORS to allow cross origin requests. The
`/api/process_query` endpoint extracts the query, use case, provider
and model from the request body.

It then calls `get_llm()` to either return a LangChain `ChatOpenAI` or
a dictionary describing the Groq client. When the provider is Groq, the
code uses direct `call_groq()` logic; otherwise it constructs LangChain
chains.

For example, the summary use case builds a prompt like
```
Fasse den folgenden Text in einer {length}-Zusammenfassung zusammen...
```
and parses the JSON result using `JsonOutputParser`.

Feedback storage simply prints the document constructed from request
fields and returns it. The code hints at integration with OpenSearch,
but the actual indexing is not implemented.

### chains.py
This file defines prompt templates with LangChain's `PromptTemplate` and
Pydantic models for expected output. It also provides direct Groq helper
functions `get_fun_fact_groq`, `get_quiz_groq`, `get_summary_groq` and
`get_free_prompt_groq` using the Groq client API.

`clean_json_output` removes markdown fences and quotes from model
responses before JSON decoding. `safe_invoke` wraps chain execution and
logs parsing errors.

The `main()` function inside this file demonstrates how to use these
helpers by calling `validate_input` to check for system prompts,
obtaining the LLM via `get_llm` and then invoking the appropriate chain.

### validators.py
Contains simple checks to ensure that responses from the LLMs contain
the required fields. Each function returns a `(bool, message)` pair for
higher level error handling.

5. Frontend in Detail
---------------------
### chat/src/App.vue
The Vue component maintains the conversation state. Key data fields are:
- `useCase` – selected functionality such as Summary or Quiz.
- `provider` and `model` – chosen LLM provider and model name.
- `messages` – array of chat history entries including quiz results.
The template displays a sidebar for choosing use cases, providers and
models, plus a main chat area. When the user submits a query
(`sendQuery()` method), a fetch request is made to the backend.

If the backend returns a quiz result, the component builds a quiz object
and pushes it to the chat as a question. Other result types are rendered
as markdown via `marked` and sanitized using `DOMPurify`.

Each bot message can be rated with thumbs up/down. Ratings trigger a
POST request to `/api/store_feedback`.

The component also prompts for overall chat satisfaction after five
messages.

### chat/Dockerfile
This container installs Node dependencies and starts Vite in development
mode on port 5173. The `vite.config.js` binds the server to `0.0.0.0` so
Docker can expose it.

### Dockerfile.fastapi
The backend image uses Python 3.11-slim. Dependencies are installed in a
builder stage, then copied into a final minimal image that runs Uvicorn
with the app.

### docker-compose.yml
Defines two services: `backend` and `frontend`. The backend exposes port
8033 and loads environment variables from `.env`. The frontend container
exposes port 3033 and depends on the `chat` directory.

6. Running the Application
--------------------------
1. Ensure Docker and Docker Compose are installed.
2. Place API keys in `.env` as shown in [README.md lines 84-92](./README.md).
3. Run `docker-compose up --build`.
4. Access the frontend at `http://localhost:3033` and the API at
   `http://localhost:8033/api/process_query`.
5. Choose a use case, type your query and select provider/model in the
   UI.

7. Technology Overview
----------------------
- **FastAPI**: Python web framework for building APIs quickly. Offers
  type hints and automatic docs. In this project it serves JSON
  endpoints. Its limitation here is that complex session or database
  handling is not implemented.
- **LangChain**: Abstraction layer for LLM interactions. Used for
  prompt templates and output parsers in `chains.py`. While powerful, it
  introduces dependency on its parsing logic which may fail when models
  deviate from expected formats.
- **Groq Client**: Direct API calls to models hosted by Groq. Provides
  access to advanced reasoning models. Limits: requires valid API key
  and is tied to Groq's available models.
- **OpenAI Client**: Used via `langchain_openai.ChatOpenAI`. Standard
  interface to OpenAI models. Rate limits and cost apply.
- **Vue 3 with Vite**: Lightweight frontend framework. Handles UI logic
  and state management directly in `App.vue`. The project does not use a
  router or state library, so complexity is minimal but scalability is
  limited.
- **Docker**: Packages backend and frontend. Simplifies deployment but
  adds build overhead when dependencies change.
- **OpenSearch (planned)**: Mentioned in `.env` and README, but feedback
  is only printed. Indexing could store thumbs up/down data for later
  analysis.

8. Weaknesses
-------------
- **No persistence**: Feedback is printed to the console rather than
  stored. Without a database, user ratings cannot be analyzed.
- **Limited error handling**: If the LLM returns unexpected JSON, the
  user receives a generic error. Recovery strategies are minimal.
- **Hardcoded model lists**: Available models are manually specified in
  `App.vue`, requiring redeployment to add or remove entries.
- **Security**: The `.env` file with real API keys is present in the
  repository, which is unsafe for public code.
- **Scalability**: The frontend stores messages in memory only. Long
  conversations beyond 10 messages are truncated.
- **Missing tests**: No automated tests are provided for backend or
  frontend logic.

9. Possible Improvements
------------------------
- Implement persistent storage for feedback, perhaps using OpenSearch or
  a relational database. Connect `store_feedback` to an indexing
  function.
- Add authentication to protect API keys and restrict usage.
- Introduce environment-based configuration for available models rather
  than hardcoding them.
- Write unit tests for `chains.py` and `main.py` to ensure validation and
  parsing behave correctly.
- Use async streaming responses for LLM calls to improve perceived
  latency.
- Refactor the frontend into smaller components for maintainability and
  incorporate a router for additional pages.
- Implement rate limiting and logging middleware in FastAPI for better
  monitoring.

10. Code Explanation Summary
----------------------------
- `get_llm()` selects the correct LLM client. When provider is Groq it
  returns a dictionary containing the Groq client and model string
  (lines 34-49 of `src/chains.py`). For other providers it returns a
  `ChatOpenAI` instance.
- Prompt templates such as `quiz_prompt` define the text instructions for
  generating a quiz question (lines 60-103). The parser ensures the
  model responds in JSON.
- `call_groq()` builds a request body for Groq's API with optional
  `reasoning_format` for certain models (lines 120-138). The helper
  functions for each use case call this method and parse the response
  using `clean_json_output`.
- In `main.py`, each use case path constructs the chain and uses
  `safe_invoke` to catch parsing errors (lines 24-129). Validation via
  `validate_response` ensures the returned JSON conforms to expected
  fields.
- The Vue component `sendQuery()` composes the POST body and pushes user
  and bot messages to the `messages` array (around line 96 of
  `App.vue`). It converts the full conversation to the format expected by
  the backend via `getContextMessages()`.

11. Conclusion
--------------
HBVGPT combines FastAPI, LangChain and a simple Vue interface to create
an extendable AI assistant. Although the repository demonstrates the
core interactions between frontend, backend and LLM providers, adding
persistent storage, proper security, automated tests and modular
frontend structure would make it production ready.
