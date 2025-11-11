# Deploying to Render

This guide walks you through deploying the MRN/NRIC masking application to Render.

## Prerequisites

1. **GitHub Repository**: Push your code to GitHub
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **Tesseract OCR**: Render's Python environment includes Tesseract by default

## Deployment Steps

### Option 1: Using render.yaml (Blueprint) - Recommended

This deploys both backend and frontend automatically.

1. **Push to GitHub**
   ```powershell
   git add .
   git commit -m "Deploy to Render"
   git push origin main
   ```

2. **Create Blueprint on Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click **"New" → "Blueprint"**
   - Connect your GitHub repository
   - Render will detect `render.yaml` and create both services

3. **Configure Environment Variables** (after creation)
   - Backend service: No additional variables needed
   - Frontend service: Ensure `VITE_API_URL` points to your backend URL
     - Example: `https://no-mrn-api.onrender.com`

4. **Wait for Deploy**
   - Backend: ~3-5 minutes
   - Frontend: ~2-3 minutes

### Option 2: Manual Deployment

#### Backend (Web Service)

1. **Create New Web Service**
   - Dashboard → New → Web Service
   - Connect GitHub repo
   - Configure:
     - **Name**: `no-mrn-api`
     - **Environment**: Python 3
     - **Region**: Choose closest to your users
     - **Branch**: main
     - **Root Directory**: (leave blank)
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`

2. **Environment Variables**
   - `PYTHON_VERSION` = `3.12.0` (optional, Render auto-detects)

3. **Health Check**
   - Path: `/health`

4. **Deploy** - Click "Create Web Service"

#### Frontend (Static Site)

1. **Create New Static Site**
   - Dashboard → New → Static Site
   - Connect same GitHub repo
   - Configure:
     - **Name**: `no-mrn-frontend`
     - **Branch**: main
     - **Root Directory**: `frontend/frontend`
     - **Build Command**: `npm install && npm run build`
     - **Publish Directory**: `dist`

2. **Environment Variables**
   - `VITE_API_URL` = `https://your-backend-name.onrender.com`
     - Replace with your actual backend URL from step 1

3. **Deploy** - Click "Create Static Site"

### After Deployment

1. **Update CORS in Backend**
   
   Edit `server.py` to add your frontend URL:
   ```python
   allowed_origins = [
       "http://localhost:5173",
       "http://127.0.0.1:5173",
       "https://your-frontend-name.onrender.com",  # Add this
   ]
   ```

2. **Test the Application**
   - Visit your frontend URL: `https://your-frontend-name.onrender.com`
   - Upload a test image
   - Verify masking works and downloads correctly

3. **Check Logs** (if issues occur)
   - Backend logs: Render Dashboard → your-backend-service → Logs
   - Frontend build logs: Render Dashboard → your-frontend-site → Events

## Important Notes

### Free Tier Limitations

- **Backend**: Free tier sleeps after 15 min inactivity (cold starts ~30s)
- **Storage**: No persistent storage - uploaded files are temporary
- **Bandwidth**: 100 GB/month on free tier

### Tesseract on Render

Render's Python environment includes Tesseract OCR by default. The auto-detection in `no_mrn.py` works, but you can also set explicitly:

```python
# In no_mrn.py, update if needed:
if os.name == "posix":  # Linux on Render
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
```

### Production Optimizations

1. **Disable Debug Mode**
   - In `server.py`, set `debug=False` in `mask_nric_in_image()` call

2. **Add Rate Limiting** (optional)
   ```powershell
   pip install slowapi
   ```
   Then configure in `server.py`

3. **Environment Variables**
   - Store sensitive config in Render's Environment Variables section
   - Access via `os.getenv("VAR_NAME")`

## Troubleshooting

### Backend Issues

**Problem**: Service crashes on startup
- **Check**: Logs for missing dependencies
- **Fix**: Ensure `requirements.txt` is complete

**Problem**: OCR not working
- **Check**: Tesseract installation in logs
- **Fix**: Usually auto-installed; verify with `which tesseract` in shell

**Problem**: CORS errors
- **Check**: Frontend URL is in `allowed_origins`
- **Fix**: Update `server.py` and redeploy

### Frontend Issues

**Problem**: Can't connect to backend
- **Check**: `VITE_API_URL` environment variable
- **Fix**: Set correct backend URL and rebuild

**Problem**: Build fails
- **Check**: Node version (Render uses Node 18+ by default)
- **Fix**: Add `.node-version` file if needed

## Custom Domain (Optional)

1. Go to your service settings
2. Click "Custom Domains"
3. Add your domain and configure DNS

## Monitoring

- **Health Checks**: Backend at `/health`
- **Logs**: Real-time in Render dashboard
- **Metrics**: View in service dashboard

## Cost Estimate

- **Free Tier**: Both services free with limitations
- **Paid**: ~$7/month per service for always-on instances

## Support

- [Render Docs](https://render.com/docs)
- [Render Community](https://community.render.com)
