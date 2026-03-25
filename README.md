# 🩺 MediAssist — AI Medical Chatbot

A stateless, async AI-powered medical assistant chatbot built with **FastAPI** and **Groq API** (free LLM access), deployable on AWS EC2 with Nginx as a reverse proxy.

---

## 📁 Project Structure

```
mediassist/
├── main.py                 ← FastAPI async backend
├── static/
│   └── index.html          ← Frontend chat UI
├── .env                    ← Your secrets (never commit this!)
├── .env.example            ← Safe template to commit to git
├── .gitignore              ← Prevents secrets from being pushed
├── requirements.txt        ← Python dependencies
├── mediassist.service      ← systemd service (auto-start on EC2)
├── nginx.conf              ← Nginx reverse proxy config
└── README.md               ← This file
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (async Python) |
| LLM | Groq API — `llama-3.3-70b-versatile` (free) |
| HTTP Client | `httpx.AsyncClient` (non-blocking) |
| Server | Uvicorn (ASGI) |
| Reverse Proxy | Nginx |
| Process Manager | systemd |
| Frontend | Vanilla HTML + CSS + JS |

---

## 🖥️ Local Development Setup (Windows)

### Step 1 — Clone the repo

```cmd
git clone https://github.com/yourusername/mediassist.git
cd mediassist
```

### Step 2 — Install uv (fast Python package manager)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.sh | iex"
```

Restart your terminal, then verify:

```cmd
uv --version
```

### Step 3 — Create virtual environment

```cmd
uv venv
```

### Step 4 — Activate virtual environment

```cmd
.venv\Scripts\activate
```

You should see `(.venv)` at the start of your terminal line — this means it is active.

### Step 5 — Install dependencies

```cmd
uv pip install -r requirements.txt
```

### Step 6 — Configure environment variables

```cmd
copy .env.example .env
```

Open `.env` in any text editor and fill in your Groq API key:

```
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=llama-3.3-70b-versatile
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
```

> **How to get a free Groq API key:**
> 1. Go to [https://console.groq.com](https://console.groq.com)
> 2. Sign up for a free account
> 3. Navigate to API Keys → Create API Key
> 4. Copy and paste it into your `.env` file

### Step 7 — Run the app locally

```cmd
uvicorn main:app --reload --port 8000
```

Open your browser and go to:

```
http://localhost:8000
```

The `--reload` flag automatically restarts the server when you save changes to your code. Remove this flag in production.

---

## 🐙 Pushing to GitHub

### Step 1 — Initialize git

```cmd
git init
```

### Step 2 — Stage all files

```cmd
git add .
```

### Step 3 — Remove .env from tracking (important!)

```cmd
git rm --cached .env
```

### Step 4 — Verify .env is NOT listed

```cmd
git status
```

Make sure `.env` does **not** appear in the staged files list before proceeding. Only `.env.example` should be present.

### Step 5 — Commit

```cmd
git commit -m "initial commit - mediassist chatbot"
```

### Step 6 — Connect to your GitHub repo

```cmd
git remote add origin https://github.com/yourusername/mediassist.git
git branch -M main
git push -u origin main
```

> **Note:** GitHub no longer accepts passwords. When prompted, use a Personal Access Token as your password.
> Generate one at: GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic) → select `repo` scope.

### Subsequent pushes

```cmd
git add .
git commit -m "your update message"
git push
```

---

## ☁️ AWS EC2 Deployment

### Prerequisites

Before starting, make sure your EC2 instance has these **Security Group inbound rules** configured:

| Port | Protocol | Purpose |
|---|---|---|
| 22 | TCP | SSH access |
| 80 | TCP | HTTP (public web traffic) |
| 443 | TCP | HTTPS (after adding SSL) |

Recommended instance: **Ubuntu 22.04 LTS**, t2.micro or larger.

---

### Step 1 — Connect to your EC2 instance

From your local machine (Mac/Linux terminal or Windows PowerShell):

```bash
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>
```

If you get a permissions error on the key file:

```bash
chmod 400 your-key.pem
```

---

### Step 2 — Update system and install packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git nginx
```

---

### Step 3 — Clone your project from GitHub

```bash
git clone https://github.com/yourusername/mediassist.git /home/ubuntu/mediassist
cd /home/ubuntu/mediassist
```

---

### Step 4 — Create virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### Step 5 — Configure environment variables on the server

```bash
cp .env.example .env
nano .env
```

Fill in your Groq API key and set DEBUG to false:

```
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=llama-3.3-70b-versatile
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
```

Save and exit: `Ctrl+X` → `Y` → `Enter`

---

### Step 6 — Test the app manually first

Before setting up services, verify the app runs correctly:

```bash
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open your browser and visit:

```
http://<EC2-PUBLIC-IP>:8000
```

If it loads correctly, press `Ctrl+C` to stop and move to the next step.

---

### Step 7 — Set up systemd service

The systemd service keeps your app running 24/7, starts it automatically on server boot, and restarts it if it ever crashes.

```bash
sudo cp mediassist.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mediassist
sudo systemctl start mediassist
```

Check it is running:

```bash
sudo systemctl status mediassist
```

You should see `Active: active (running)` in green.

View live logs:

```bash
sudo journalctl -u mediassist -f
```

---

### Step 8 — Set up Nginx as reverse proxy

Nginx sits on port 80 (the standard public HTTP port) and forwards all traffic to your FastAPI app running on port 8000. This means users access your app at `http://yoursite.com` without needing to type `:8000`.

```bash
sudo cp nginx.conf /etc/nginx/sites-available/mediassist
sudo ln -s /etc/nginx/sites-available/mediassist /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

Your app is now publicly accessible at:

```
http://<EC2-PUBLIC-IP>
```

---

### Step 9 — (Optional) Add HTTPS with Let's Encrypt

If you have a domain name pointed to your EC2 instance, you can add a free SSL certificate:

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

Certbot automatically updates your Nginx config and renews the certificate every 90 days.

---

## 🔄 How to Update Your Deployment

When you push new code to GitHub, update your EC2 instance like this:

```bash
cd /home/ubuntu/mediassist
git pull
sudo systemctl restart mediassist
```

---

## 🛠️ Useful Commands

| Task | Command |
|---|---|
| Start app | `sudo systemctl start mediassist` |
| Stop app | `sudo systemctl stop mediassist` |
| Restart app | `sudo systemctl restart mediassist` |
| Check app status | `sudo systemctl status mediassist` |
| View live logs | `sudo journalctl -u mediassist -f` |
| Health check | `curl http://localhost:8000/health` |
| Restart Nginx | `sudo systemctl restart nginx` |
| Check Nginx config | `sudo nginx -t` |
| View Nginx logs | `sudo tail -f /var/log/nginx/error.log` |

---

## 🏗️ Architecture Overview

```
Internet
    │
    │  port 80 / 443
    ▼
 Nginx (reverse proxy)
    │
    │  port 8000 (internal only)
    ▼
 FastAPI + Uvicorn  (main.py)
    │
    │  HTTPS API call
    ▼
 Groq API  (LLM response)
    │
    ▼
 Response back to user
```

**Stateless design:** No database, no sessions, no history stored on the server. Each user's conversation lives only in their browser tab. When the tab closes, the history is gone.

---

## ❓ Common Issues

**App not starting — check logs:**
```bash
sudo journalctl -u mediassist -f
```

**Nginx 502 Bad Gateway — app is not running:**
```bash
sudo systemctl restart mediassist
sudo systemctl status mediassist
```

**Port 8000 not accessible from browser — that is correct.** Port 8000 is internal only. Always access via port 80 through Nginx.

**`.env` accidentally pushed to GitHub:**
```bash
git rm --cached .env
git commit -m "remove .env from tracking"
git push
```
Then immediately rotate your Groq API key at [console.groq.com](https://console.groq.com).
