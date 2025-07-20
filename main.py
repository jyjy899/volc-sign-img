import os
from fastapi import FastAPI, HTTPException, Query
import uvicorn
from volcengine.CV import CVService  # 官方 SDK

REGION = "cn-north-1"

svc = CVService(region=REGION)
svc.set_ak(os.getenv("VOLC_ACCESS_KEY_ID"))
svc.set_sk(os.getenv("VOLC_SECRET_ACCESS_KEY"))
svc.set_host("visual.volcengineapi.com")          # 必须设置

ACTION  = "JimengHighAESGeneralV21L"              # 接口名

app = FastAPI()

@app.get("/gen_image")
async def gen_image(prompt: str = Query(..., description="提示词")):
    body = {
        "prompt": prompt,
        "req_key": "jimeng_high_aes_general_v21_l",
        "return_url": True
    }
    try:
        # 官方 SDK 自动完成签名、重试、解析
        resp = svc.common_handler(ACTION, {}, body)
        img_url = resp["Result"]["image_urls"][0]
        return {"image_url": img_url}
    except Exception as e:
        # SDK 内部已抛出带错误码/信息的异常
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
