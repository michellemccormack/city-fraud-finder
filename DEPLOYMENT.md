# Deployment Guide

This FastAPI application can be deployed to various platforms. Here are the most straightforward options:

## Option 1: Render (Easiest - Recommended)

**Pros**: Free tier, automatic HTTPS, easy setup, handles databases

1. **Create account** at https://render.com
2. **Create a new Web Service** from your GitHub repo (or connect via GitHub)
3. **Settings**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3
4. **Add Environment Variable**:
   - `DB_URL`: `sqlite:///./city_fraud_finder.db` (or upgrade to Postgres later)
5. **Deploy!**

Your app will be live at `https://your-app-name.onrender.com`

---

## Option 2: Railway

**Pros**: Free tier, simple deployment, good for Python apps

1. Go to https://railway.app
2. **New Project** → **Deploy from GitHub repo**
3. Railway auto-detects Python
4. Add environment variable if needed: `DB_URL`
5. Deploy!

---

## Option 3: Fly.io

**Pros**: Free tier, global deployment, good performance

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Initialize: `fly launch` (from project directory)
4. Deploy: `fly deploy`

---

## Option 4: Your Own Server (VPS)

If you have your own server (DigitalOcean, Linode, AWS EC2, etc.):

### Quick Setup with systemd:

1. **Install dependencies** on your server:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv nginx
   ```

2. **Clone your code** to `/opt/city-fraud-finder` (or your preferred location)

3. **Set up virtual environment**:
   ```bash
   cd /opt/city-fraud-finder
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Create systemd service** (`/etc/systemd/system/city-fraud-finder.service`):
   ```ini
   [Unit]
   Description=City Fraud Finder API
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/opt/city-fraud-finder
   Environment="PATH=/opt/city-fraud-finder/.venv/bin"
   ExecStart=/opt/city-fraud-finder/.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. **Start service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable city-fraud-finder
   sudo systemctl start city-fraud-finder
   ```

6. **Set up Nginx reverse proxy** (`/etc/nginx/sites-available/city-fraud-finder`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

7. **Enable site**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/city-fraud-finder /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

8. **Set up SSL** (Let's Encrypt):
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

---

## Important Notes

### Database Considerations

- **SQLite (current)**: Works great for development and small deployments
  - Single file database
  - No separate database server needed
  - Good for up to ~100k records
  - **Note**: On platforms like Render, the filesystem is ephemeral - data resets on deploy unless you use a persistent volume

- **PostgreSQL (production)**: Better for production
  - Change `DB_URL` to: `postgresql://user:pass@host:5432/dbname`
  - Add `psycopg2-binary` to `requirements.txt`
  - Update SQLAlchemy connection string

### Environment Variables

Create a `.env` file (or set in hosting platform):
```
DB_URL=sqlite:///./city_fraud_finder.db
```

### Security Considerations

1. **Don't commit `.env` files** - add to `.gitignore`
2. **Use environment variables** for sensitive data
3. **Enable HTTPS** in production (Render/Railway do this automatically)
4. **Consider adding authentication** if the data is sensitive

### Updating Your App

- **Render/Railway**: Push to GitHub → auto-deploys
- **Fly.io**: Run `fly deploy`
- **VPS**: `git pull` → restart service with `sudo systemctl restart city-fraud-finder`

---

## Quick Start Recommendation

**For fastest deployment**: Use **Render.com**
- Free tier available
- Connect your GitHub repo
- Automatic HTTPS
- Takes ~5 minutes to set up

Your app will be live at: `https://city-fraud-finder.onrender.com` (or your chosen name)

