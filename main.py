# main.py
#
# 调用流程：
#   1. FastAPI 暴露 GET /gen_image?prompt=xxx
#   2. 读取环境变量中的 AK/SK（不写死在代码里）
#   3. 使用 volcengine 官方 SDK 自动签名
#   4. 指定 endpoint = "visual.volcengineapi.com"
#   5. 返回 {"image_url": "..."} 给调用方
#
import os, json
from fastapi import FastAPI, Query
from volcengine.CV.CV import CVService
import uvicorn

# 1) 从环境变量里读取 AK、SK
#    — 你在 Render 的 Environment 页面已经填过，不要写死到代码里
AK = os.getenv("VOLC_ACCESS_KEY_ID")
SK = os.getenv("VOLC_SECRET_ACCESS_KEY")

# 2) 初始化官方 SDK：指定 region = "cn-beijing"
svc = CVService(region="cn-beijing")
svc.set_ak(AK)           # 把 AK 注入 SDK
svc.set_sk(SK)           # 把 SK 注入 SDK
# 3) 关键一步！告诉 SDK 使用视觉服务专属域名
svc.set_endpoint("visual.volcengineapi.com")

app = FastAPI()

@app.get("/gen_image")
async def gen_image(prompt: str = Query(..., description="提示词")):
    """
    调用 Jimeng 高质量生图 V2.1L
    文档：https://www.volcengine.com/docs/1062/1313205
    """
    body = {
        "req_key": "jimeng_high_aes_general_v21l",
        "text": prompt,
        "n": 1,
        "style": 0,
        "width": 1024,
        "height": 1024,
        "req_type": "text2img"
    }
    # SDK 帮我们负责加 Action/Version 并自动签名
    resp = svc.common_handler(
        service="cv",
        version="2024-06-06",
        action="JimengHighAESGeneralV21L",
        params={},            # query string (这里留空)
        body=body             # JSON body
    )
    data = json.loads(resp)
    return {"image_url": data["Result"]["image_urls"][0]}

# 本地调试用；Render 部署会读取 Procfile 或 Start Command
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
