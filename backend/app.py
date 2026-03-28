from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import logging
import base64
import httpx
import random
import time
import os
import re
import json
import asyncio

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("comedy-backend")

app = FastAPI(title="Virtual Comedy Show")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === DIRECTLY EMBED API KEYS HERE ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
GOOGLE_TRENDS_API_KEY = os.getenv("GOOGLE_TRENDS_API_KEY")

# ---------------------------------------------------------
# Comedy Personas
# ---------------------------------------------------------
COMEDY_PERSONAS = {
    "the_overthinker": {
        "name": "The Anxious Overthinker",
        "guideline": "An anxious comedian who worries about simple things and turns them into funny, easy laughs."
    },
    "the_grumpy_skeptic": {
        "name": "The Grumpy Skeptic",
        "guideline": "A grumpy comedian who complains about everyday stuff with simple, funny grumbles."
    },
    "the_energetic_oddball": {
        "name": "The Energetic Oddball",
        "guideline": "A lively comedian who makes silly, funny connections about regular life."
    },      
    "the_smooth_storyteller": {
        "name": "The Smooth Storyteller",
        "guideline": "A smooth comedian who tells funny, easy stories with a big laugh at the end."
    }
}

# ---------------------------------------------------------
# Voice Configuration (ElevenLabs)
# ---------------------------------------------------------
VOICE_IDS = {
    "conversational": "pNInz6obpgDQGcFmaJgB",
    "quirky": "jBpfuIE2acCO8z3wKNLl",
    "storytelling": "XrExE9yKIg1WjnnlVkGX",
    "deep": "nPczCjzI2devNBz1zQrb",
    "sarcastic": "yoZ06aMxZJJ28mfd3POQ",
    "childlike": "zrHiDhphv9ZnVXBqCLjz"
}

VOICE_SETTINGS = {
    "conversational": {"stability": 0.7, "similarity_boost": 0.9},
    "quirky": {"stability": 0.6, "similarity_boost": 0.9},
    "storytelling": {"stability": 0.7, "similarity_boost": 0.8},
    "deep": {"stability": 0.7, "similarity_boost": 0.9},
    "sarcastic": {"stability": 0.6, "similarity_boost": 0.9},
    "childlike": {"stability": 0.6, "similarity_boost": 0.9}
}

# ---------------------------------------------------------
# MODELS
# ---------------------------------------------------------
class JokeRequest(BaseModel):
    persona: str

class SynthesizeRequest(BaseModel):
    text: str
    persona: str

# ---------------------------------------------------------
# SERVE 3D MODEL OR FRONTEND
# ---------------------------------------------------------
@app.get("/model1.glb")
async def serve_model1_glb():
    possible_paths = [
        Path(__file__).parent / "model1.glb",
        Path(__file__).parent / "frontend" / "model1.glb",
        Path("model1.glb"),
        Path("frontend/model1.glb")
    ]
    
    for glb_path in possible_paths:
        if glb_path.exists():
            logger.info(f"✅ Serving model from: {glb_path}")
            return FileResponse(
                glb_path, 
                media_type="model/gltf-binary",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Cache-Control": "public, max-age=3600"
                }
            )
    
    logger.error(f"❌ model1.glb not found")
    raise HTTPException(status_code=404, detail="model1.glb not found")

@app.get("/")
async def serve_index():
    for path in ["index.html", "frontend/index.html"]:
        if Path(path).exists():
            return FileResponse(path)
    raise HTTPException(status_code=404, detail="index.html not found")

# ---------------------------------------------------------
# REAL-TIME, VARIED THEMES
# ---------------------------------------------------------
TRENDS_API_URL = "https://trends.googleapis.com/v1beta/search/trends/daily"

async def fetch_trending_phrase() -> str:
    api_key = GOOGLE_TRENDS_API_KEY or GEMINI_API_KEY
    non_trending_themes = ["rainy days", "old TVs", "car troubles", "long lines", "bad Wi-Fi", "loud neighbors", "cheap shoes", "forgotten passwords"]
    
    if random.choice([True, False]):
        logger.info("🎣 Using non-trending theme")
        return random.choice(non_trending_themes)
    
    if not api_key or api_key == "YOUR_GOOGLE_TRENDS_API_KEY_HERE":
        logger.warning("No Trends API key; using fallback")
        return random.choice(["coffee", "phones", "weather", "pizza", "traffic", "shopping", "TV shows", "work"])
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Goog-Api-Key": api_key
    }
    params = {"geo": "US", "hl": "en", "tz": -120}
    
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(TRENDS_API_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        trends = data.get("default", {}).get("trendingSearches", [])
        if trends:
            phrase = random.choice([t.get("title", {}).get("query", "funny topic") for t in trends])
            logger.info(f"🎣 Using trending topic: {phrase}")
            return phrase.strip()
        return "funny topic"
    except Exception as e:
        logger.warning(f"Could not fetch trends: {e}")
        return random.choice(["coffee", "phones", "weather", "pizza", "traffic", "shopping", "TV shows", "work"])

@app.post("/api/generate_joke")
async def generate_joke(req: JokeRequest):
    try:
        persona_key = req.persona
        persona_data = COMEDY_PERSONAS.get(persona_key)
        if not persona_data:
            raise HTTPException(status_code=400, detail=f"Unknown persona: {persona_key}")

        guideline = persona_data["guideline"]
        topic = await fetch_trending_phrase()
        logger.info(f"🎣 Topic seed: {topic}")

        prompt = f"""
You are a professional stand-up comedian doing a **live 2-minute set**.

Persona: {guideline}

A wild thought about **"{topic}"** just hit you out of nowhere!
Build a **completely fresh, 250-350 word routine** that's punchy and hilarious.

Rules:
- Start with a surprised reaction like 'Whoa!' or 'Wait!'
- Use super simple language with funny, relatable ideas.
- Pack in 2-3 big laughs and a funny ending.
- Write in SHORT sentences (5-15 words each).
- Use only dialogue, no stage directions, no session IDs, no numbers.
- Keep it quick, punchy, and hilarious.
- DO NOT include any session numbers, IDs, or technical markers.

Topic: "{topic}"
"""

        gen_config = {
            "temperature": 1.3,
            "topK": 60,
            "topP": 0.95,
            "maxOutputTokens": 1500
        }

        safety_settings = [
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"}
        ]

        model_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

        for attempt in range(2):  # Reduced retries for speed
            async with httpx.AsyncClient(timeout=40.0) as client:  # Reduced timeout
                res = await client.post(
                    model_url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": gen_config,
                        "safetySettings": safety_settings
                    }
                )

            if res.status_code == 429:
                await asyncio.sleep(3 * attempt)
                continue

            if res.status_code != 200:
                logger.error(f"Gemini HTTP {res.status_code}: {res.text[:500]}")
                raise Exception(f"Gemini API error {res.status_code}: {res.text[:100]}")

            data = res.json()
            logger.info(f"Gemini raw response keys: {list(data.keys())}")

            candidates = data.get("candidates", [])
            if not candidates:
                logger.error(f"No candidates in response: {json.dumps(data, indent=2)[:1000]}")
                logger.info("Possible safety block—check promptFeedback: ", data.get("promptFeedback", {}))
                break

            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            if not parts:
                logger.error(f"No parts in candidate: {json.dumps(candidate, indent=2)[:500]}")
                logger.info("Finish reason: ", candidate.get("finishReason"))
                break

            script = parts[0].get("text", "").strip()
            if not script:
                logger.error(f"Empty text in parts: {json.dumps(parts, indent=2)[:300]}")
                break

            # Clean up script - remove any session/ID markers
            script = re.sub(r'\[SESSION-\d+-[\d.]+\]', '', script)
            script = re.sub(r'Show ID: [\d-]+', '', script)
            script = re.sub(r'\(|\)', '', script)
            script = re.sub(r'#+\s*', '', script)
            script = re.sub(r'\s+', ' ', script).strip()

            sentences = [s.strip() for s in re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', script) if s.strip()]
            ssml_script = ' '.join([f'{sent}<break time="0.5s"/>' for sent in sentences])

            logger.info(f"✅ Generated {len(script.split())} words, {len(sentences)} sentences")
            return {
                "success": True,
                "phrases": sentences,
                "full_script": script,
                "ssml_script": ssml_script,
                "topic": topic,
                "persona": persona_key
            }

        logger.warning("Using fallback script—check Gemini key/quota/safety!")
        fallback_script = f"""Whoa, {topic}? Wait a minute—that's the craziest thing I've heard all week! You know, I was just thinking about how {topic} always sneaks up on you. Like, one minute you're fine, next you're knee-deep in chaos. Take me, for example. Last time {topic} happened, I panicked. Called my mom at 3 AM. She said, 'Honey, breathe.' But how? It's {topic}! Everything spirals. My coffee spills. Dog starts barking. Neighbors think I'm nuts. And the laughs? Oh, they come later. When you realize {topic} is just life saying, 'Surprise!' But seriously, why does {topic} hit hardest on Mondays? Universe's joke? Anyway, thanks for listening—you're the best crowd ever! Goodnight!"""
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', fallback_script)
        sentences = [s.strip() for s in sentences if s.strip()]
        ssml_script = ' '.join([f'{sent}<break time="0.5s"/>' for sent in sentences])
        return {
            "success": True,
            "phrases": sentences,
            "full_script": fallback_script,
            "ssml_script": ssml_script,
            "topic": topic,
            "persona": persona_key,
            "fallback": True
        }

    except Exception as e:
        logger.error(f"❌ Joke generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# SYNTHESIZE VOICE - OPTIMIZED FOR PARALLEL REQUESTS
# ---------------------------------------------------------
@app.post("/api/synthesize")
async def synthesize(req: SynthesizeRequest):
    try:
        if ELEVENLABS_API_KEY == "YOUR_ELEVENLABS_KEY_HERE":
            raise Exception("ElevenLabs API key not set")

        voice_id = VOICE_IDS.get(req.persona, VOICE_IDS["conversational"])
        voice_settings = VOICE_SETTINGS.get(req.persona, VOICE_SETTINGS["conversational"])

        # Clean input text of any session markers
        clean_text = re.sub(r'\[SESSION-\d+-[\d.]+\]', '', req.text)
        clean_text = re.sub(r'Show ID: [\d-]+', '', clean_text).strip()

        logger.info(f"🎤 Synthesizing {len(clean_text.split())} words")
        
        # Single attempt with optimized settings for parallel processing
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:  # Shorter timeout for parallel
                response = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
                    json={
                        "text": clean_text,
                        "model_id": "eleven_turbo_v2_5",  # FASTEST MODEL!
                        "voice_settings": {
                            "stability": voice_settings["stability"],
                            "similarity_boost": voice_settings["similarity_boost"],
                            "use_speaker_boost": False  # Disable for speed
                        },
                        "output_format": "mp3_22050_32",  # Lower quality = faster generation
                        "optimize_streaming_latency": 4  # Max optimization for speed
                    }
                )

            if response.status_code == 200:
                audio_data = response.content
                logger.info(f"✅ Audio: {len(audio_data)} bytes")
                return {
                    "success": True,
                    "audio_base64": base64.b64encode(audio_data).decode("utf-8"),
                    "duration_estimate": len(clean_text.split()) * 0.3
                }
            else:
                error_detail = response.text[:200]
                logger.error(f"❌ ElevenLabs {response.status_code}: {error_detail}")
                return {"success": False, "error": f"API Error {response.status_code}"}
                
        except httpx.TimeoutException:
            logger.error(f"⏱️ Timeout generating audio")
            return {"success": False, "error": "Timeout"}

    except Exception as e:
        logger.error(f"❌ Voice synthesis error: {e}")
        return {"success": False, "error": str(e)}

# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------
@app.get("/api/health")
async def health():
    trends_key_ok = GOOGLE_TRENDS_API_KEY and GOOGLE_TRENDS_API_KEY != "GOOGLE_TRENDS_API_KEY"
    return {
        "status": "healthy",
        "gemini_key": "✅" if GEMINI_API_KEY else "❌",
        "elevenlabs_key": "✅" if ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != "ELEVEN_LABS_API_KEY" else "❌",
        "trends_key": "✅" if trends_key_ok else "❌"
    }

# ---------------------------------------------------------
# MAIN ENTRY
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("\n🎭 Virtual Comedy Show Backend Running")
    print("=" * 50)
    print(f"Gemini API Key: {'✅ Set' if GEMINI_API_KEY and GEMINI_API_KEY != 'GOOGLE_GEMENI_API_KEY' else '⚠️ CHECK/REPLACE'}")
    print(f"ElevenLabs API Key: {'✅ Set' if ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != 'ELEVEN_LABS_API_KEY' else '❌ Missing'}")
    print(f"Trends API Key: {'✅ Set' if GOOGLE_TRENDS_API_KEY and GOOGLE_TRENDS_API_KEY != 'GOOGLE_TRENDS_API_KEY' else '❌ Missing (using fallback)'}")
    print("→ Visit http://localhost:8000 | Get new Gemini key: ai.google.dev")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)