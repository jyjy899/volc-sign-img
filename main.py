# main.py
import os, json, time, hashlib, hmac, httpx
from fastapi import FastAPI, HTTPException, Query
import uvicorn

ACCESS_KEY = os.getenv("VOLC_ACCESS_KEY_ID")
SECRET_KEY = os.getenv("VOLC_SECRET_ACCESS_KEY")

REGION = "cn-north-1"
HOST = "visual.volcengineapi.com"
SERVICE = "cv"
ACTION = "JimengHighAESGeneralV21L"
VERSION = "2024-06-06"

app = FastAPI()

def _sign(body: str, timestamp: str):
    signed_headers = "host;x-content-sha256;x-date"
    content_sha256 = hashlib.sha256(body.encode()).hexdigest()
    canonical = (
        f"POST\n/\n\n"
        f"host:{HOST}\n"
        f"x-content-sha256:{content_sha256}\n"
        f"x-date:{timestamp}\n\n"
        f"{signed_headers}\n"
        f"{content_sha256}"
    )
    date = timestamp[:8]
    k_date = hmac.new(("HMAC-SHA256"+SECRET_KEY).encode(), date.encode(), hashlib.sha256).digest()
    k_region = hmac.new(k_date, REGION.encode(), hashlib.sha256).digest()
    k_service = hmac.new(k_region, SERVICE.encode(), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, b"request", hashlib.sha256).digest()
    signature = hmac.new(k_signing, canonical.encode(), hashlib.sha256).hexdigest()

    scope = f"{date}/{REGION}/{SERVICE}/request"
    auth = f"HMAC-SHA256 Credential={ACCESS_KEY}/{scope}, SignedHeaders={signed_headers}, Signature={signature}"
    return auth, content_sha256

async def _call_volc(prompt: str):
    body_dict = {
        "req_key": ACTION.lower(),
        "text": prompt,
        "n": 1,
        "style": 0,
        "width": 1024,
        "height": 1024,
        "req_type": "text2img"
    }
    body = json.dumps(body_dict, separators=(",",":"))
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    auth, sha = _sign(body, ts)

    headers = {
        "Content-Type": "application/json",
        "Host": HOST,
        "X-Content-Sha256": sha,
        "X-Date": ts,
        "Authorization": auth
    }
    url = f"https://{HOST}/?Action={ACTION}&Version={VERSION}"
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(url, data=body, headers=headers)
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    return r.json()["body"]["Result"]["image_urls"][0]

@app.get("/gen_image")
async def gen_image(prompt: str = Query(..., description="提示词")):
    img = await _call_volc(prompt)
    return {"image_url": img}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
