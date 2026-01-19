# Deployment Guide

## Quick Deploy: Vercel + Render (Free)

### Prerequisites
- GitHub account
- Supabase project (already set up)

---

## Step 1: Push to GitHub

```bash
cd /home/snigdha/reverse_tune/slmgen
git add .
git commit -m "Add deployment configs"
git remote add origin https://github.com/YOUR_USERNAME/slmgen.git
git push -u origin master
```

---

## Step 2: Deploy Backend to Render

1. Go to [render.com](https://render.com) and sign up
2. Click **New** → **Blueprint**
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml`
5. **Add environment variables** in dashboard:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `JWT_SECRET`
6. Click **Apply**

Your API will be at: `https://slmgen-api.onrender.com`

---

## Step 3: Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com) and sign up
2. Click **Add New** → **Project**
3. Import your GitHub repo
4. Set **Root Directory** to `slmgenui`
5. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://slmgen-api.onrender.com`
   - `NEXT_PUBLIC_SUPABASE_URL` = your Supabase URL
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` = your Supabase key
6. Click **Deploy**

Your app will be at: `https://slmgen.vercel.app`

---

## Step 4: Update CORS

After both are deployed, update Render env var:
```
ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

---

## Alternative: Railway (One-Click)

For simpler deployment, use Railway:

1. Go to [railway.app](https://railway.app)
2. Click **New Project** → **Deploy from GitHub**
3. Select your repo
4. Add both services manually

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS errors | Update `ALLOWED_ORIGINS` in Render |
| API timeouts | Render free tier sleeps after 15min inactivity |
| Build fails | Check Python/Node versions |

---

## Free Tier Limits

| Service | Limit |
|---------|-------|
| Vercel | 100GB bandwidth, unlimited deploys |
| Render | 750 hours/month, sleeps after 15min |
| Supabase | 500MB database, 1GB storage |
