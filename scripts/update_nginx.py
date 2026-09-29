path = "/etc/nginx/sites-available/default"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

header_block = """        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0" always;
        add_header Pragma "no-cache" always;
        add_header Expires "0" always;
"""

if "Cache-Control" not in text:
    text = text.replace('proxy_set_header Connection "upgrade";', 'proxy_set_header Connection "upgrade";\n' + header_block)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Updated nginx config with no-cache headers")
else:
    print("Already has Cache-Control")
