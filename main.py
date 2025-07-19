# main.py  –  极简 SDK 版
import os, json, asyncio
from fastapi import FastAPI, Query
from volcengine.CV.CV import CVService

AK = os.getenv("VOLC_ACCESS_KEY_ID")
SK = os.getenv("VOLC_SECRET_ACCESS_KEY")

svc = CVService(region="cn-north-1")
svc.set_ak(AK)
svc.set_sk(SK)

app = FastAPI()

@app.get("/gen_image")
async def gen_image(prompt: str = Query(..., description="提示词")):
    # JimengHighAESGeneralV21L 需要的业务参数
    body = {
        "req_key": "jimeng_high_aes_general_v21l",
        "text": prompt,
        "n": 1,
        "style": 0,
        "width": 1024,
        "height": 1024,
        "req_type": "text2img"
    }
    # SDK 自动帮我们补 Action/Version 并计算签名
    resp = svc.common_handler(
        "cv",                  # service
        "2024-06-06",          # version
        "JimengHighAESGeneralV21L",  # action
        {}, body               # query={}, body=json
    )
    data = json.loads(resp)
    return {"image_url": data["Result"]["image_urls"][0]}
