# 🚀 MobiPrice — Server Deployment & Systemd Guide

Ushbu qo'llanma **MobiPrice** platformasini toza Linux (Ubuntu 22.04 / 24.04 yoki Debian) serveriga o'rnatish, ishga tushirish va uzluksiz boshqarish bo'yicha to'liq yo'riqnomadir.

---

## 1. Talablar
- Ubuntu 22.04 / 24.04 LTS
- Python 3.11+
- Nginx
- SQLite3
- Certbot (SSL uchun)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip nginx sqlite3 certbot python3-certbot-nginx
```

---

## 2. Loyihani Serverga Joylashtirish
Loyiha kodini `/var/www/mobiprice` papkasiga joylang:

```bash
sudo mkdir -p /var/www/mobiprice
sudo chown -R $USER:$USER /var/www/mobiprice
cd /var/www/mobiprice

# Git orqali yuklash:
git clone https://github.com/kadirkulovv/MobiPrice.git .

# Virtual muhit yaratish va kutubxonalarni o'rnatish:
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# .env konfiguratsiyasini yaratish:
cp .env.example .env  # Token va kalitlarni to'ldiring
nano .env

# Statik fayllarni yig'ish va migratsiyalarni tekshirish:
python manage.py collectstatic --noinput
python manage.py migrate

# Ruxsatlarni to'g'rilash (www-data foydalanuvchisi uchun):
sudo chown -R www-data:www-data /var/www/mobiprice
sudo chmod -R 775 /var/www/mobiprice/media
sudo chmod 664 /var/www/mobiprice/db.sqlite3
```

---

## 3. Systemd Servislarni O'rnatish va Faollashtirish

Loyihaning `deploy/` papkasidagi tayyor `.service` fayllarini tizimga ko'chiring:

```bash
# 1. Servislarni nusxalash:
sudo cp /var/www/mobiprice/deploy/mobiprice_web.service /etc/systemd/system/
sudo cp /var/www/mobiprice/deploy/mobiprice_bot.service /etc/systemd/system/

# 2. Systemd-ni qayta yuklash:
sudo systemctl daemon-reload

# 3. Veb-sayt va Telegram bot servisini avtomatik ishga tushirish (Auto-start on boot):
sudo systemctl enable --now mobiprice_web
sudo systemctl enable --now mobiprice_bot

# 4. Holatini tekshirish:
sudo systemctl status mobiprice_web
sudo systemctl status mobiprice_bot
```

---

## 4. Nginx va Bepul SSL (Let's Encrypt) Sozlash

```bash
# Nginx konfiguratsiyasini ulash:
sudo cp /var/www/mobiprice/deploy/nginx_mobiprice.conf /etc/nginx/sites-available/mobiprice
sudo ln -s /etc/nginx/sites-available/mobiprice /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Nginx sintaksisini tekshirish:
sudo nginx -t

# Nginx-ni qayta ishga tushirish:
sudo systemctl restart nginx

# Bepul SSL sertifikatini olish (Avtomatik HTTPS):
sudo certbot --nginx -d mobi-price.uz -d www.mobi-price.uz
```

---

## 5. Avtomatik Zaxira (Cron Backup) Sozlash

Har kechasi soat 03:00 da `db.sqlite3` va `media/` arxivlanadi:

```bash
# Cron jadvaliga qo'shish:
crontab -e

# Quyidagi qatorni qo'shing:
0 3 * * * /var/www/mobiprice/deploy/backup_db.sh >> /var/log/mobiprice_backup.log 2>&1
```

---

## 6. Foydali Buyruqlar

- Sayt loglarini ko'rish: `sudo journalctl -u mobiprice_web -f`
- Bot loglarini ko'rish: `sudo journalctl -u mobiprice_bot -f`
- Saytni qayta ishga tushirish: `sudo systemctl restart mobiprice_web`
- Botni qayta ishga tushirish: `sudo systemctl restart mobiprice_bot`
