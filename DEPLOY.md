# MediAssist — EC2 Deployment Guide

## Prerequisites
- EC2 instance: Ubuntu 22.04 LTS, t2.micro or larger
- Security Group inbound rules:
  - Port 22   (SSH)
  - Port 80   (HTTP)
  - Port 443  (HTTPS, if using SSL)

---

## 1. Connect to your EC2 instance

```bash
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>
```

---

## 2. Install system packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git nginx
```

---

## 3. Clone or upload your project

```bash
# Option A — Git
git clone https://github.com/your-repo/medical_chatbot.git /home/ubuntu/medical_chatbot

# Option B — SCP from local machine
scp -i your-key.pem -r ./medical_chatbot ubuntu@<EC2-PUBLIC-IP>:/home/ubuntu/
```

---

## 4. Create virtual environment and install dependencies

```bash
cd /home/ubuntu/medical_chatbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 5. Configure environment variables

```bash
cp .env.example .env
nano .env
# Set GROQ_API_KEY=your_actual_key
```

---

## 6. Test the app manually first

```bash
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
# Visit http://<EC2-PUBLIC-IP>:8000 to verify
# Ctrl+C to stop
```

---

## 7. Set up systemd service (runs on boot, auto-restarts)

```bash
sudo cp mediassist.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mediassist
sudo systemctl start mediassist

# Check status
sudo systemctl status mediassist

# View logs
sudo journalctl -u mediassist -f
```

---

## 8. Set up Nginx as reverse proxy

```bash
sudo cp nginx.conf /etc/nginx/sites-available/mediassist
sudo ln -s /etc/nginx/sites-available/mediassist /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default     # remove default site
sudo nginx -t                                # test config
sudo systemctl restart nginx
```

Now your app is accessible at **http://<EC2-PUBLIC-IP>** (port 80).

---

## 9. (Optional) Add HTTPS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

---

## Useful commands

| Task | Command |
|---|---|
| Restart app | `sudo systemctl restart mediassist` |
| View live logs | `sudo journalctl -u mediassist -f` |
| Update code | `git pull && sudo systemctl restart mediassist` |
| Health check | `curl http://localhost:8000/health` |
