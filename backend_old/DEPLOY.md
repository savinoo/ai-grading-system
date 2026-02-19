# 🚀 Deployment Guide - AI Grading System

## Streamlit Cloud Deployment (Recommended)

### Prerequisites
1. GitHub account
2. Google Gemini API key (free tier: https://aistudio.google.com/app/apikey)

### Steps

#### 1. Push to GitHub
```bash
git push origin feature/professor-assistant
# Or merge to main and push main
```

#### 2. Deploy on Streamlit Cloud

1. Go to: https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Configure:
   - **Repository:** `savinoo/ai-grading-system`
   - **Branch:** `feature/professor-assistant` (or `main` if merged)
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
ngrok http 8502
```

Copy the `https://xxxx.ngrok.io` URL and share it.

---

## Environment Variables

The app reads secrets from:
1. `.streamlit/secrets.toml` (local)
2. Streamlit Cloud Secrets (cloud)
3. Environment variables (fallback)

Required:
- `GOOGLE_API_KEY` - Gemini API key

Optional:
- `LANGSMITH_API_KEY` - For tracing/observability
- `MODEL_NAME` - Default: `gemini-2.0-flash`
- `TEMPERATURE` - Default: `0`

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
1. Use PostgreSQL instead of JSON for student data
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
