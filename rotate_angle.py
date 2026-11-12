"""根据参考图库识别 UUSEC 旋转验证码的角度。"""

import base64
import glob
import io
import os
import sys
import time

import cv2
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright


TARGET = sys.argv[1] if len(sys.argv) > 1 else "http://target.example/"
REF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")

mask = np.zeros((120, 120), dtype=np.uint8)
cv2.circle(mask, (60, 60), 52, 255, -1)
MASK_BOOL = mask > 0

REFERENCES = []
for filename in sorted(glob.glob(os.path.join(REF_DIR, "*.png"))):
    name = os.path.basename(filename)
    image = np.array(Image.open(filename).convert("RGBA"))
    image_h, image_w = image.shape[:2]
    scale = 104.0 / max(image_w, image_h)
    new_w, new_h = int(image_w * scale), int(image_h * scale)
    gray = cv2.resize(cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY), (new_w, new_h)).astype(np.float32)
    canvas = np.zeros((120, 120), dtype=np.float32)
    offset_x, offset_y = (120 - new_w) // 2, (120 - new_h) // 2
    canvas[offset_y:offset_y + new_h, offset_x:offset_x + new_w] = gray
    rotated = {}
    for angle in range(360):
        matrix = cv2.getRotationMatrix2D((60, 60), angle, 1.0)
        rotated[angle] = cv2.warpAffine(
            canvas, matrix, (120, 120), flags=cv2.INTER_LINEAR
        ).ravel()[MASK_BOOL.ravel()]
    REFERENCES.append({"name": name, "rotated": rotated})

print(f"已加载 {len(REFERENCES)} 张参考图，每张预生成 360 个角度。")


def match_angle(target_image):
    """先每隔 3 度粗搜索，再在最佳角度附近逐度细查。"""
    target = np.array(target_image.convert("L"), dtype=np.float32).ravel()[MASK_BOOL.ravel()]
    target = target - target.mean()
    target_norm = np.linalg.norm(target)
    best = {"name": "", "angle": 0, "correlation": -1}

    for reference in REFERENCES:
        for angle in range(0, 360, 3):
            candidate = reference["rotated"][angle]
            candidate = candidate - candidate.mean()
            score = float(
                np.dot(target, candidate)
                / (target_norm * np.linalg.norm(candidate) + 1e-10)
            )
            if score > best["correlation"]:
                best = {"name": reference["name"], "angle": angle, "correlation": score}

    for angle in range(max(0, best["angle"] - 3), min(359, best["angle"] + 4)):
        for reference in REFERENCES:
            if reference["name"] != best["name"]:
                continue
            candidate = reference["rotated"][angle]
            candidate = candidate - candidate.mean()
            score = float(
                np.dot(target, candidate)
                / (target_norm * np.linalg.norm(candidate) + 1e-10)
            )
            if score > best["correlation"]:
                best = {"name": reference["name"], "angle": angle, "correlation": score}
    return best


playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=True)
page = browser.new_page(viewport={"width": 500, "height": 500})
api_data = {}


def on_response(response):
    """从页面响应中收集验证码 token 和图片。"""
    if "/captcha/info" in response.url and response.status == 200:
        try:
            api_data["token"] = response.json()["msg"]
        except (ValueError, KeyError):
            pass
    if "/captcha/img" in response.url and response.status == 200:
        try:
            api_data["image_bytes"] = response.body()
        except Exception:
            pass


page.on("response", on_response)
page.goto(TARGET, timeout=15000, wait_until="networkidle")
page.wait_for_selector("#captchaImage", timeout=10000)
time.sleep(0.3)

token = api_data.get("token")
image_bytes = api_data.get("image_bytes")
if not image_bytes:
    encoded = page.evaluate("document.getElementById('captchaImage').toDataURL('image/png')")
    image_bytes = base64.b64decode(encoded.split(",")[1])

print(f"Token：{token}")
result = match_angle(Image.open(io.BytesIO(image_bytes)).convert("RGBA"))
print(f"参考图：{result['name']}")
print(f"旋转角度：{result['angle']} 度")
print(f"相关系数：{result['correlation']:.4f}")

response = page.evaluate(
    f"""
    (async () => {{
        const response = await fetch('/api/v1/captcha/verify?id={token}&angle={result['angle']}');
        return await response.json();
    }})()
    """
)
print(f"验证响应：{response}")
print("验证成功。" if response.get("code") == 0 else "验证失败。")

browser.close()
playwright.stop()
