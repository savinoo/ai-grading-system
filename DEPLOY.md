# 🚀 Deployment Guide - AI Grading System

## Streamlit Cloud Deployment (Recommended)

### Prerequisites
1. GitHub account
2. Google Gemini API key (free tier: https://aistudio.google.com/app/apikey)

### Steps

#### 1. Push to GitHub
```bash
git push origin main
```

#### 2. Deploy on Streamlit Cloud

1. Go to: https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Configure:
   - **Repository:** `savinoo/ai-grading-system`
   - **Branch:** `main`
   - **Main file path:** `app/main.py`
5. Click "Deploy"

#### 3. Configure Secrets

In the Streamlit Cloud dashboard:
1. Go to **App settings** (⚙️) > **Secrets**
2. Add the following:

```toml
GOOGLE_API_KEY = "your-actual-gemini-api-key"
MODEL_NAME = "gemini-2.0-flash"
TEMPERATURE = "0"

# Optional: LangSmith observability
LANGSMITH_API_KEY = "your-langsmith-key"
LANGSMITH_PROJECT_NAME = "ai-grading-system"
```

3. Click "Save"
4. App will restart automatically

#### 4. Access Your App

Your app will be live at:
```
https://[your-app-name].streamlit.app
```

---

## Alternative: Local with ngrok

For quick sharing without cloud deployment:

```bash
# Install ngrok
brew install ngrok

# Start Streamlit locally
streamlit run app/main.py

# In another terminal, expose it
ngrok http 8501
```

Copy the `https://xxxx.ngrok.io` URL and share it.

---

## Option 3: Docker

```bash
docker build -t ai-grading-system .
docker run -p 8501:8501 \
  -e LLM_PROVIDER=local \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  ai-grading-system
```

> Note: Requires Ollama running on host machine. Use `http://host.docker.internal:11434` to reach the host from inside the container.

For cloud LLM providers:
```bash
docker run -p 8501:8501 \
  -e LLM_PROVIDER=gemini \
  -e GOOGLE_API_KEY=your-key \
  ai-grading-system
```

Or use Docker Compose:
```bash
docker compose up
```

---

## Environment Variables

The app reads secrets from:
1. `.streamlit/secrets.toml` (local)
2. Streamlit Cloud Secrets (cloud)
3. Environment variables (fallback)

### Complete Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `local` | LLM backend: `local` (Ollama), `gemini`, or `openai` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL (when `LLM_PROVIDER=local`) |
| `LOCAL_MODEL_NAME` | `llama3.2` | Ollama model name (when `LLM_PROVIDER=local`) |
| `GOOGLE_API_KEY` | - | Google Gemini API key (when `LLM_PROVIDER=gemini`) |
| `OPENAI_API_KEY` | - | OpenAI API key (when `LLM_PROVIDER=openai`) |
| `MODEL_NAME` | `gemini-2.0-flash` | Model name for cloud providers |
| `TEMPERATURE` | `0` | LLM temperature |
| `API_CONCURRENCY` | `10` | Max parallel API calls |
| `API_THROTTLE_SLEEP` | `0.3` | Delay between API calls (seconds) |
| `BATCH_CHUNK_SIZE` | `5` | Submissions per batch chunk |
| `DIVERGENCE_THRESHOLD` | `2.0` | Score diff threshold to trigger Arbiter |
| `MAX_RETRIES` | `3` | Max retry attempts for failed API calls |
| `INITIAL_RETRY_DELAY` | `2.0` | Initial retry delay (seconds) |
| `MAX_RETRY_DELAY` | `30.0` | Max retry delay (seconds) |
| `GAP_THRESHOLD` | `6.0` | Learning gap detection threshold |
| `STRENGTH_THRESHOLD` | `8.0` | Strength recognition threshold |
| `PLAGIARISM_THRESHOLD` | `0.90` | Plagiarism similarity threshold |
| `DATA_RETENTION_DAYS` | `365` | Days to keep student data |
| `LANGSMITH_API_KEY` | - | LangSmith tracing key (optional) |
| `LANGSMITH_TRACING_ENABLED` | `false` | Enable LangSmith tracing |
| `LANGSMITH_PROJECT_NAME` | `ai-grading-system` | LangSmith project name |

---

## Troubleshooting

### "Missing GOOGLE_API_KEY"
- Check Streamlit Cloud secrets are saved
- Verify API key is valid at https://aistudio.google.com/

### "Module not found"
- Ensure `requirements.txt` includes all dependencies
- Streamlit Cloud auto-installs from `requirements.txt`

### "Connection timeout"
- Free Gemini API has rate limits
- Consider upgrading or adding retry logic

---

## Production Considerations

For production deployment:
1. Consider PostgreSQL for multi-user concurrent access (current SQLite implementation works well for single-user/small deployments)
2. Add authentication (Streamlit supports OAuth)
3. Set up monitoring (Streamlit Cloud has built-in analytics)
4. Configure custom domain
5. Enable HTTPS (automatic on Streamlit Cloud)

---

## Security Notes

- Never commit API keys to git
- Use `.streamlit/secrets.toml` locally (gitignored)
- Use Streamlit Cloud Secrets for deployment
- Rotate keys periodically

---

## Support

Issues? Open a GitHub issue or contact Lucas.
