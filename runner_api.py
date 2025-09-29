import base64
import requests
import json
import torch
from PIL import Image
import json
import base64
from io import BytesIO


# 2. 构造输入
instruction = "请点击屏幕上的‘会员’按钮"  # 示例指令
image_path = "assets/test.jpeg"  # 你的图片路径
image = Image.open(image_path).convert("RGB")

# 3. 将图片长边缩放至1120以降低计算和显存压力
def __resize__(origin_img):
    resolution = origin_img.size
    w,h = resolution
    max_line_res = 1120
    if max_line_res is not None:
        max_line = max_line_res
        if h > max_line:
            w = int(w * max_line / h)
            h = max_line
        if w > max_line:
            h = int(h * max_line / w)
            w = max_line
    img = origin_img.resize((w,h),resample=Image.Resampling.LANCZOS)
    return img
image = __resize__(image)


def encode_image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

image_base64 = encode_image_to_base64(image)

# 构造消息格式
# instruction = "请根据当前屏幕截图判断下一步操作"
# messages = [{
#     "role": "user",
#     "content": [
#         f"<Question>{instruction}</Question>\n当前屏幕截图：",
#         {
#             "type": "image_url",
#             "image_url": {
#                 "url": f"data:image/png;base64,{image_base64}"
#             }
#         }
#     ]
# }]

ACTION_SCHEMA = json.load(open('eval/utils/schema/schema.json', encoding="utf-8"))
ACTION_SCHEMA["required"] = ["thought"]  # 启用 thought 字段

SYSTEM_PROMPT = f'''# Role
你是一名熟悉安卓系统触屏GUI操作的智能体，将根据用户的问题，分析当前界面的GUI元素和布局，生成相应的操作。

# Task
针对用户问题，根据输入的当前屏幕截图，输出下一步的操作。

# Rule
- 以紧凑JSON格式输出
- 输出操作必须遵循Schema约束

# Schema
{json.dumps(ACTION_SCHEMA, indent=None, ensure_ascii=False, separators=(',', ':'))}'''


import requests

response = requests.post(
    # "http://localhost:11434/api/chat",
    url="http://localhost:11434/v1/chat/completions",
    headers={"Content-Type": "application/json"},
    json={
        "model": "agentcpm:latest",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"<Question>{instruction}</Question>\n当前屏幕截图：",},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/png;base64,{image_base64}",
                    },
                ],
            },
        ],
        "stream": False,
    },
)

# 输出结果
print(response.json())
