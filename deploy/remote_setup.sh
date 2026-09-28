#!/bin/bash
set -e

echo "=== 1. Setting up Nginx default site ==="
cat << 'EOF' > /etc/nginx/sites-available/default
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

nginx -t
systemctl reload nginx

echo "=== 2. Restarting systemd services ==="
systemctl daemon-reload
systemctl restart oge-web oge-bot

sleep 3
echo "=== 3. Checking status ==="
systemctl status oge-web --no-pager
systemctl status oge-bot --no-pager
