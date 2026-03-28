# 🎤 Virtual Comedy Show AI

An AI-powered virtual stand-up comedy experience featuring a 3D animated performer, real-time joke generation, and expressive voice synthesis.

---

## 🚀 Features

* 🎭 Multiple comedy personas

  * Anxious Overthinker
  * Grumpy Skeptic
  * Energetic Oddball
  * Smooth Storyteller

* 🤖 AI-generated stand-up routines (Google Gemini API)

* 🔊 Realistic voice synthesis (ElevenLabs)

* 🌐 Dynamic topics using trends + random themes

* 🎨 3D animated comedian (Three.js)

* 💬 Subtitle + synchronized audio playback

* 🎬 Full show flow (Intro → Performance → Encore)

---

## 🛠️ Tech Stack

### 🔹 Backend

* FastAPI
* Uvicorn
* HTTPX
* Python

### 🔹 Frontend

* HTML, CSS, JavaScript
* Three.js (3D rendering)

### 🔹 APIs Used

* Google Gemini API
* ElevenLabs API
* Google Trends API

---

## 📂 Project Structure

```
Virtual-Standup-Comedy-Show/
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── model1.glb
│
├── render.yaml
├── run.sh
├── .gitignore
└── README.md
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository

```bash
git clone https://github.com/nitishbavalatti/Virtual-Stand-Up-Comedy-Show.git
cd Virtual-Stand-Up-Comedy-Show
```

---

### 2️⃣ Create virtual environment

```bash
python -m venv venv
```

#### Activate:

* Windows:

```bash
venv\Scripts\activate
```

* Mac/Linux:

```bash
source venv/bin/activate
```

---

### 3️⃣ Install dependencies

```bash
pip install -r backend/requirements.txt
```

---

### 4️⃣ Setup environment variables

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
GOOGLE_TRENDS_API_KEY=your_google_trends_key
```

---

## ▶️ Run the Project

### Run backend

```bash
uvicorn backend.app:app --reload
```

### Open in browser

```
http://localhost:8000
```

---

## 🌍 Deployment (Render)

This project is ready for deployment using Render.

* Uses `render.yaml`
* Auto deploy from GitHub
* Add API keys in Render dashboard → Environment Variables

---

## 🔐 Security Note

❗ Do NOT commit API keys directly in code
Always use environment variables (`.env`)

---

## 🎬 How It Works

1. User selects a persona + voice
2. Backend generates a comedy script using AI
3. Script is split into phrases
4. Audio is generated for each phrase
5. Frontend plays audio + subtitles
6. 3D model performs the show

---

## 📸 Demo (Add Later)

* Add screenshots or GIF here
* Example:

```
![Demo](demo.gif)
```

---

## 💡 Future Improvements

* 🎤 Live audience reactions
* 🧠 Memory-based humor (context-aware jokes)
* 🌍 Multi-language comedy
* 📱 Mobile optimization
* 🎭 Custom avatar upload

---

## 🙌 Acknowledgements

* FastAPI
* Three.js
* ElevenLabs
* Google Gemini API

---

## 📜 License

MIT License

---

## 👨‍💻 Author

Nitish RB
(Feel free to connect & contribute 🚀)
