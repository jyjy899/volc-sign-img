# main.py
#
# ① FastAPI 暴露 GET /gen_image?prompt=xxx
# ② 手写 HMAC-SHA256 签名 —— 已补 Canonical QueryString
# ③ Host = visual.volcengineapi.com   Region = cn-beijing
# ④ 返回 {"image_url": "..."} 给调用方
#
import os, json, time, hmac, hashlib, httpx
from fastapi import FastAPI, HTTPException, Query
import uvicorn

ACCESS_KEY = os.getenv("VOLC_ACCESS_KEY_ID")
SECRET_KEY = os.getenv("VOLC_SECRET_ACCESS_KEY")

REGION   = "cn-beijing"
HOST     = "visual.volcengineapi.com"
SERVICE  = "cv"
ACTION   = "JimengHighAESGeneralV21L"
VERSION  = "2024-06-06"

# ---------- 签名工具（已补 query） ----------------------------
def sign(body: str, timestamp: str) -> tuple[str, str]:
    signed_headers = "host;x-content-sha256;x-date"
    content_sha256 = hashlib.sha256(body.encode()).hexdigest()

    # ⚠️ Canonical QueryString 必须包含 Action&Version 且按字典序
    canonical_query = f"Action={ACTION}&Version={VERSION}"

    canonical_request = (
        f"POST\n/\n{canonical_query}\n"
        f"host:{HOST}\n"
        f"x-content-sha256:{content_sha256}\n"
        f"x-date:{timestamp}\n\n"
        f"{signed_headers}\n"
        f"{content_sha256}"
    )

    date = timestamp[:8]
    k_date    = hmac.new(("HMAC-SHA256" + SECRET_KEY).encode(), date.encode(),   hashlib.sha256).digest()
    k_region  = hmac.new(k_date,    REGION.encode(),  hashlib.sha256).digest()
    k_service = hmac.new(k_region,  SERVICE.encode(), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, b"request",       hashlib.sha256).digest()

    signature = hmac.new(k_signing, canonical_request.encode(), hashlib.sha256).hexdigest()
    credential_scope = f"{date}/{REGION}/{SERVICE}/request"
    authorization = (
        f"HMAC-SHA256 Credential={ACCESS_KEY}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    return authorization, content_sha256
# -------------------------------------------------------------

async def call_volc(prompt: str) -> str:
    body_dict = {
        "req_key": ACTION.lower(),
        "text": prompt,
        "n": 1,
        "style": 0,
        "width": 1024,
        "height": 1024,
        "req_type": "text2img"
    }
    body = json.dumps(body_dict, separators=(",", ":"))
    ts   = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    auth, sha = sign(body, ts)

    headers = {
        "Content-Type":     "application/json",
        "Host":             HOST,
        "X-Content-Sha256": sha,
        "X-Date":           ts,
        "Authorization":    auth
    }
    url = f"https://{HOST}/?Action={ACTION}&Version={VERSION}"
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(url, data=body, headers=headers)
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    data = r.json()
    return data["body"]["Result"]["image_urls"][0]

# ---------------- FastAPI ------------------------------
app = FastAPI()

@app.get("/gen_image")
async def gen_image(prompt: str = Query(..., description="随便写提示词")):
    img =
