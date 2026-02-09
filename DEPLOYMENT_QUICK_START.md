# Deploying to Render - Quick Start

## ✅ Files Created for Deployment

Your app is now **deployment-ready** with these files:

- ✅ `start.sh` - Runs both FastAPI and Streamlit
- ✅ `render.yaml` - Render configuration
- ✅ `runtime.txt` - Python 3.10 specification
- ✅ `DEPLOY.md` - Full deployment guide

## 🚀 Deploy in 3 Steps

### 1️⃣ Push to GitHub

```bash
git init
git add .
git commit -m "TMS AI - Ready for Render deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/tms-ai.git
git push -u origin main
```

### 2️⃣ Deploy on Render

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml`
5. Add environment variables:
   - `MISTRAL_API_KEY`
   - `GROQ_API_KEY`
6. Click **"Create Web Service"**

### 3️⃣ Access Your App

After deployment:
- **Streamlit UI**: `https://your-app.onrender.com:8501`
- **API Docs**: `https://your-app.onrender.com:8000/docs`

## 🔧 Environment Variables Required

Set in Render Dashboard → Environment:

```
MISTRAL_API_KEY=your_mistral_key
GROQ_API_KEY=your_groq_key
API_BASE_URL=http://localhost:8000
```

## 📝 Important Notes

- **Free tier** sleeps after 15 min inactivity
- **Cold start** takes 30-60 seconds
- Add **persistent disk** for ChromaDB storage
- See `DEPLOY.md` for detailed instructions

---

**Your app is ready to deploy!** 🎉
