<template>
  <div id="app">
    <div class="sidebar">
      <h2>Team Paiya</h2>

      <div class="usecase-grid">
        <div
          class="usecase-tile"
          v-for="(label, key) in useCases"
          :key="key"
          :class="{ active: useCase === key }"
          @click="selectUseCase(key)"
        >
          <span class="emoji">{{ label.icon }}</span>
          <span class="text">{{ label.name }}</span>
        </div>
      </div>

      <div class="tile-group">
        <div class="tile-label">🧠 Provider wählen:</div>
        <div class="tile-grid">
          <div
            v-for="p in Object.keys(availableModels)"
            :key="p"
            class="tile-button"
            :class="{ active: provider === p }"
            @click="provider = p"
          >
            {{ p }}
          </div>
        </div>
      </div>

      <div class="tile-group" v-if="availableModels[provider]">
        <div class="tile-label">🎯 Modell wählen:</div>
        <div class="tile-scroll-list">
          <div
            v-for="m in availableModels[provider]"
            :key="m"
            class="tile-button"
            :class="{ active: model === m }"
            @click="model = m"
          >
            {{ m }}
          </div>
        </div>
      </div>

      <p style="margin-top: 1rem; font-size: 0.85rem;">
        Aktives Modell: <strong>{{ model }}</strong>
      </p>
    </div>

    <div class="main">
      <div v-if="quizWarning" class="quiz-warning-banner">
        ❗ Bitte beantworte zuerst die aktuelle Quizfrage.
      </div>
      <div v-if="showChatRating && !chatRated" class="chat-rating-banner">
        <p>Wie zufrieden bist du mit dem Chat?</p>
        <button @click="submitChatRating('up')">😊</button>
        <button @click="submitChatRating('down')">🙁</button>
      </div>

      <div class="header">
        <h3>Willkommen bei HBVGPT</h3>
        <p>Nutze KI, um deinen Arbeitsalltag effizienter zu gestalten.</p>
      </div>
      <div v-if="!useCase" class="central-usecases">
      <h3>Wähle einen Anwendungsfall</h3>
      <div class="central-usecase-grid">
        <div
          v-for="(label, key) in useCases"
          :key="key"
          class="central-usecase-tile"
          @click="selectUseCase(key)"
        >
          <div class="icon">{{ label.icon }}</div>
          <div class="name">{{ label.name }}</div>
          <div class="description">
            <template v-if="key === 'Summary'">Fasse Texte schnell und präzise zusammen.</template>
            <template v-else-if="key === 'Quiz'">Erstelle ein Quiz zu deinem Wunschthema.</template>
            <template v-else-if="key === 'FreePrompt'">Stelle beliebige Fragen oder gib Prompts ein.</template>
            <template v-else-if="key === 'FunFact'">Erhalte interessante Fakten mit Quellenangabe.</template>
          </div>
        </div>
      </div>
    </div>


      <div class="chatbox">
        <div class="chat">
          <div v-for="(entry, index) in messages.filter(e => e.type !== 'hidden')" :key="index">
            <div v-if="entry.type !== 'quiz'" :class="['chat-entry', entry.sender]">
              <div class="avatar">
                <img
                  :src="entry.sender === 'bot' ? botAvatar : userAvatar"
                  :alt="entry.sender === 'bot' ? 'Bot' : 'User'"
                  class="avatar-img"
                />
              </div>

              <div>
                <div class="bubble">
                  <template v-if="typeof entry.text === 'string'">
                    <div v-html="renderMarkdown(entry.text)"></div>
                  </template>
                  <template v-else>
                    <div v-html="renderMarkdown(entry.text.text)"></div>
                    <div class="source">
                      Quelle:
                      <a :href="entry.text.source" target="_blank" rel="noopener noreferrer">
                        {{ entry.text.source }}
                      </a>
                    </div>
                  </template>
                </div>

                <div class="rating-below" v-if="entry.sender === 'bot'">
                  <button
                    :class="{ selected: chatRatings[index] === 'up' }"
                    @click="rateMessage(index, 'up')"
                    title="Gefällt mir"
                  >
                    👍
                  </button>
                  <button
                    :class="{ selected: chatRatings[index] === 'down' }"
                    @click="rateMessage(index, 'down')"
                    title="Gefällt mir nicht"
                  >
                    👎
                  </button>
                </div>
              </div>
            </div>

            <div v-else class="quiz-box">
              <h3>{{ entry.quiz.question }}</h3>
              <ul>
                <li v-for="(opt, i) in entry.quiz.options" :key="i">
                  <button
                    @click="checkAnswer(entry.quiz, opt)"
                    :disabled="entry.quiz.selected !== null"
                  >
                    {{ opt }}
                  </button>
                </li>
              </ul>
              <p v-if="entry.quiz.selected !== null">
                <strong>
                  {{ entry.quiz.selected === entry.quiz.answer
                    ? '✅ Richtig!'
                    : '❌ Falsch. Richtige Antwort: ' + entry.quiz.answer }}
                </strong>
              </p>
              <p
                v-if="entry.quiz.selected !== null && entry.quiz.explanation"
                style="margin-top: 0.5rem; font-size: 0.95rem;"
              >
                💡 <em>{{ entry.quiz.explanation }}</em>
              </p>
            </div>
          </div>
        </div>

        <div class="controls">
          <select v-if="useCase === 'Summary'" v-model="length">
            <option disabled value="">Zusammenfassungslänge wählen</option>
            <option>kurz</option>
            <option>mittel</option>
            <option>lang</option>
          </select>

          <div v-if="useCase === 'Quiz'">
            <label style="font-weight: bold;">📚 Thema wählen:</label>
            <select v-model="selectedTopic">
              <option disabled value="">Thema auswählen</option>
              <option v-for="topic in topics" :key="topic" :value="topic">{{ topic }}</option>
              <option value="custom">Anderes Thema...</option>
            </select>
            <input
              v-if="selectedTopic === 'custom'"
              v-model="customTopic"
              type="text"
              placeholder="Eigenes Thema eingeben"
              style="margin-top: 0.5rem;"
            />
          </div>

          <textarea
            v-if="useCase && useCase !== 'Quiz'"
            v-model="query"
            rows="2"
            placeholder="Deine Eingabe..."
            :disabled="!useCase"
            @keyup.enter.exact="handleEnter"
          ></textarea>

          <button @click="sendQuery">Senden</button>
        </div>
      </div>
    </div>
  </div>
</template>


<script>
import { marked } from 'marked';
import DOMPurify from 'dompurify';

export default {
  data() {
    return {
      useCase: '',
      query: '',
      quizWarning: false,
      length: '',
      provider: 'groq',
      model: 'gemma2-9b-it',
      selectedTopic: '',
      customTopic: '',
      topics: ['Technologie', 'Geschichte', 'Wissenschaft', 'Gesundheit', 'Kunst'],
      messages: [],
      chatRatings: {},
      showChatRating: false,
      chatRated: false,
      availableModels: {
        openai: ['gpt-4o', 'gpt-3.5-turbo'],
        groq: [
          'gemma2-9b-it',
          'compound-beta-mini',
          'qwen-qwq-32b',
          'deepseek-r1-distill-llama-70b',
          'llama-3.3-70b-versatile',
          'allam-2-7b',
          'llama-3.1-8b-instant',
          'llama-guard-3-8b',
          'llama3-70b-8192',
          'llama3-8b-8192',
          'meta-llama/llama-4-maverick-17b-128e-instruct',
          'meta-llama/llama-4-scout-17b-16e-instruct',
          'mistral-saba-24b'
        ]
      },
      useCases: {
        Summary: { name: 'Zusammenfassung', icon: '📄' },
        Quiz: { name: 'Quiz', icon: '🔍' },
        FreePrompt: { name: 'Freies Prompten', icon: '💬' },
        FunFact: { name: 'Fun Fact', icon: '✨' }
      },
      botAvatar: 'https://cdn-icons-png.flaticon.com/512/4712/4712107.png',
      userAvatar: 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'
    };
  },
  watch: {
    provider(newProvider) {
      this.model = this.availableModels[newProvider][0];
    }
  },
  methods: {
    selectUseCase(caseName) {
      this.useCase = caseName;
      this.messages = [];
      this.query = '';
      this.length = '';
      this.selectedTopic = '';
      this.customTopic = '';
      this.chatRatings = {};
      this.chatRated = false;
      this.showChatRating = false;
    },
    handleEnter() {
      if (!this.query || !this.useCase || (this.useCase === 'Quiz' && !this.selectedTopic && !this.customTopic)) return;
      this.sendQuery();
    },
    showQuizWarning() {
    this.quizWarning = true;
    setTimeout(() => {
      this.quizWarning = false;
    }, 2500);
  },
    async sendQuery() {
    const topic = this.selectedTopic === 'custom' ? this.customTopic : this.selectedTopic;

  if (this.useCase === 'Quiz') {
    if (!topic) return;

    const lastQuiz = [...this.messages].reverse().find(m => m.type === 'quiz');
    if (lastQuiz && lastQuiz.quiz && lastQuiz.quiz.selected === null) {
      this.showQuizWarning();
      return;
    }

    this.query = topic;
  }

  if (!this.query && this.useCase !== 'Quiz') return;
  this.messages.push({ sender: 'user', type: 'text', text: this.query });

  const response = await fetch('http://localhost:8033/api/process_query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: this.query,
      use_case: this.useCase,
      length: this.length || undefined,
      provider: this.provider,
      model: this.model,
      messages: this.getContextMessages().slice(-10)
    })
  });

  const result = await response.json();

  if (result.type === 'quiz') {
    const quizObj = {
      question: result.question,
      options: result.options,
      answer: result.answer,
      explanation: result.explanation || '',
      selected: null
    };

    this.messages.push({
      sender: 'bot',
      type: 'quiz',
      quiz: quizObj
    });

    this.messages.push({
      sender: 'bot',
      type: 'hidden',
      text: `Frage: ${quizObj.question}\nAntwortmöglichkeiten:\n${quizObj.options.join('\n')}\nRichtige Antwort: ${quizObj.answer}\nErklärung: ${quizObj.explanation}`
    });
  } else {
    let botReply = '';

    if (result.type === 'free_prompt') botReply = result.response;
    else if (result.type === 'summary') botReply = result.summary;
    else if (result.type === 'fun_fact') {
      botReply = {
        text: result.fact,
        source: result.source
      };
    } else {
      botReply = result.message || 'Etwas ist schiefgelaufen...';
    }

    this.messages.push({ sender: 'bot', type: 'text', text: botReply });
  }

  if (this.messages.length >= 5 && !this.chatRated) {
    this.showChatRating = true;
  }

  if (this.messages.length > 10) {
    this.messages = this.messages.slice(this.messages.length - 10);
  }

  this.query = '';

  this.$nextTick(() => {
    const chatBox = this.$el.querySelector('.chat');
    if (chatBox) {
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  });

    },

    getContextMessages() {
      return this.messages
        .filter(m => m.sender === 'user' || m.sender === 'bot')
        .map(m => {
          let content = '';

          if (typeof m.text === 'string') {
            content = m.text;
          } else if (m.text && typeof m.text.text === 'string') {
            content = m.text.text;
          } else if (m.type === 'quiz' && m.quiz) {
            content = `Frage: ${m.quiz.question}\nAntwortmöglichkeiten:\n${m.quiz.options?.join('\n')}\nRichtige Antwort: ${m.quiz.answer}\nErklärung: ${m.quiz.explanation || ''}`;
          }

          return {
            role: m.sender === 'user' ? 'user' : 'assistant',
            content
          };
        });
    },

    checkAnswer(quiz, selectedOption) {
      if (quiz.selected !== null) return;
      quiz.selected = selectedOption;
    },

    rateMessage(index, value) {
      this.chatRatings[index] = value;

      const payload = {
        thumbs: value,
        message_index: index,
        model: this.model,
        provider: this.provider,
        feedback: this.feedback
      };

      fetch('http://localhost:8033/api/store_feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
        .then(res => res.json())
        .then(data => {
          console.log("Feedback gespeichert:", data);
        })
        .catch(err => {
          console.error("Fehler beim Feedback-Speichern:", err);
        });
    },

    submitChatRating(value) {
      this.chatRated = true;
      this.showChatRating = false;
      console.log("Gesamtrating:", value, "Einzelbewertungen:", this.chatRatings);
    },

    renderMarkdown(text) {
      return DOMPurify.sanitize(marked(text));
    }
  }
};
</script>


<style scoped>
* {
  box-sizing: border-box;
}

html, body {
  position: fixed;
  inset: 0; /* top, right, bottom, left = 0 */
  margin: 0;
  padding: 0;
  width: 100vw;
  height: 100vh;
  font-family: Arial, sans-serif;
  background: #f3f3f3;
  overflow: hidden;
}

#app {
  position: absolute;
  inset: 0;
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: row;
  overflow: hidden;
}

.sidebar {
  width: clamp(260px, 22vw, 400px);
  background-color: #002c5f;
  color: white;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.sidebar h2 {
  margin: 0 0 1rem;
  font-size: 1.5rem;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f0f4fa;
  height: 100%;
  overflow: hidden;
}

.header {
  flex-shrink: 0;
  padding: 1rem;
  background-color: #e0e9f7;
  border-bottom: 1px solid #ccc;
}

.chatbox {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
}

.chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  overflow-y: auto;
  padding: 1rem;
  scroll-behavior: smooth;
}

.chat-entry {
  display: flex;
  align-items: flex-start;
  width: 100%;
}

.chat-entry.bot {
  flex-direction: row;
}

.chat-entry.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  margin: 0 0.5rem;
  flex-shrink: 0;
}

.avatar-img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #ccc;
}

.bubble {
  max-width: 70%;
  padding: 0.75rem;
  border-radius: 10px;
  word-wrap: break-word;
  white-space: pre-wrap;
  background-color: #e0e9f7;
  color: #000;
  text-align: justify;
}

.chat-entry.user .bubble {
  background-color: #6f96c1;
  max-width: 100%;
  color: #fff;
}

.source {
  font-size: 0.85rem;
  color: #666;
  margin-top: 0.25rem;
  font-style: italic;
}

.source a {
  color: #004080;
  text-decoration: underline;
}

.controls {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background-color: #fff;
}

.controls textarea,
.controls input,
.controls select,
.controls button {
  font-size: 1rem;
  padding: 0.5rem;
}

.controls button {
  background-color: #002c5f;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.quiz-box {
  background-color: #fff3cd;
  border: 1px solid #ffeeba;
  padding: 1rem;
  margin-top: 1rem;
  border-radius: 10px;
  text-align: justify;
}

.quiz-box h3 {
  margin-bottom: 0.5rem;
}

.quiz-box ul {
  list-style-type: none;
  padding: 0;
}

.quiz-box li {
  margin-bottom: 0.5rem;
}

.quiz-box button {
  padding: 0.5rem 1rem;
  font-size: 1rem;
  background-color: #004080;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.quiz-box button:disabled {
  background-color: #999;
  cursor: not-allowed;
}

.usecase-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
}
.usecase-tile {
  display: flex;
  align-items: center;
  background-color: #004080;
  color: white;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
}

.usecase-tile:hover {
  background-color: #0055aa;
  transform: translateY(-1px);
}

.usecase-tile.active {
  background-color: #003366;
  font-weight: bold;
  box-shadow: inset 0 0 0 2px white;
}

.usecase-tile .emoji {
  font-size: 1.5rem;
  margin-right: 0.75rem;
}

.usecase-tile .text {
  font-size: 1rem;
}

.tile-group {
  margin-top: 1.5rem;
}

.tile-label {
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.tile-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.tile-button {
  background-color: #003366;
  color: white;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  text-align: center;
  transition: background-color 0.2s;
}

.tile-button:hover {
  background-color: #0055aa;
}

.tile-button.active {
  background-color: #003366;
  font-weight: bold;
  box-shadow: inset 0 0 0 2px white;
}

.tile-scroll-list {
  max-height: 180px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-right: 4px;
  margin-top: 0.5rem;
}

.tile-scroll-list::-webkit-scrollbar {
  width: 6px;
}

.tile-scroll-list::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.4);
  border-radius: 3px;
}

.central-usecases {
  padding: 2rem;
  text-align: center;
}

.central-usecase-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  justify-content: center;
  margin-top: 1rem;
}

.central-usecase-tile {
  background-color: #004080;
  color: white;
  padding: 1.5rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.central-usecase-tile:hover {
  background-color: #0055aa;
  transform: translateY(-2px);
}

.central-usecase-tile .icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.central-usecase-tile .name {
  font-size: 1.25rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.central-usecase-tile .description {
  font-size: 0.95rem;
  line-height: 1.3;
}

/* 📱 Responsive */
@media (max-width: 600px) {
  .central-usecase-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1024px) {
  #app {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }

  .main {
    flex: 1;
  }

  .sidebar h2 {
    font-size: 1.25rem;
    margin-bottom: 0;
  }
}

@media (max-width: 768px) {
  .sidebar {
    flex-direction: column;
    align-items: flex-start;
  }

  .bubble {
    max-width: 100%;
  }

  .controls {
    padding: 0.5rem;
  }

  .controls textarea,
  .controls input,
  .controls select,
  .controls button {
    font-size: 0.9rem;
    padding: 0.4rem;
  }

  .quiz-box {
    padding: 0.75rem;
  }
}
.quiz-warning-banner {
  position: absolute;
  top: 50%;
  left: 60%;
  transform: translate(-50%, -50%);
  background-color: #6fc198;
  color: #000;
  padding: 1rem 2rem;
  border-radius: 10px;
  font-weight: bold;
  box-shadow: 0 0 10px rgba(0,0,0,0.2);
  z-index: 9999;
  text-align: center;
  animation: fadeInOut 2.5s ease-in-out;
}

@keyframes fadeInOut {
  0% { opacity: 0; transform: translate(-50%, -60%); }
  10%, 90% { opacity: 1; transform: translate(-50%, -50%); }
  100% { opacity: 0; transform: translate(-50%, -40%); }
}

</style>

