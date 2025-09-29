import base64
import requests
import json
import torch
from PIL import Image
import json
import base64
from io import BytesIO
from mark_coordinates import mark_coordinates


# 将图片长边缩放至1120以降低计算和显存压力
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



def encode_image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")




ACTION_SCHEMA = json.load(open('eval/utils/schema/schema.json', encoding="utf-8"))
ACTION_SCHEMA["required"] = ["thought"]  # 启用 thought 字段

SYSTEM_PROMPT = f'''# Role
你是一名熟悉安卓系统触屏GUI操作的智能体，将根据用户的问题，分析当前界面的GUI元素和布局，生成相应的操作。

# Task
针对用户问题，根据输入的当前屏幕截图，输出下1~3步的操作。

# Rule
- 以紧凑JSON格式输出
- 输出操作必须遵循Schema约束

# Schema
{json.dumps(ACTION_SCHEMA, indent=None, ensure_ascii=False, separators=(',', ':'))}'''

def query_ollama(image_base64, instruction:str):

    url = "http://localhost:11434/v1/chat/completions"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": "agentcpm:latest",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"<Question>{instruction}</Question>\n当前屏幕截图：",
                    },
                    {
                        "type": "image_url",
                        "image_url": f"data:image/png;base64,{image_base64}",
                    },
                ],
            },
        ],
        "stream": False,
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        content = response.content
        encodings = ['utf-8', 'ascii', 'latin1']
        for encoding in encodings:
            try:
                decoded_content = content.decode(encoding)
                # 输出结果
                return json.loads(decoded_content)
            except UnicodeDecodeError:
                continue
            except json.JSONDecodeError:
                continue
        return None
    except requests.exceptions.RequestException as e:
        return None

   
    # {'id': 'chatcmpl-361', 'object': 'chat.completion', 'created': 1759130533, 'model': 'agentcpm:latest', 'system_fingerprint': 'fp_ollama', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '{"thought":"目标是点击屏幕上的‘会员’按钮。目前界面显示了音乐应用的推荐页面，‘会员’按钮位于顶部导航栏中。点击‘会员’按钮可以访问应用的会员专属页面。","POINT":[729,69]}'}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 657, 'completion_tokens': 57, 'total_tokens': 714}}

def visualize_result(model_result: dict, output_dir="./marked_images/"):
    for res in model_result['choices']:
        _res = json.loads(res['message']['content'])
        # x = 
        marked_image_path = mark_coordinates(
            image_path=image_path,
            x=731,  # Center horizontally (0-1000 scale)
            y=69,  # Slightly above center vertically (0-1000 scale)
            output_dir=output_dir,
            marker_color=(255, 0, 0),  # Red color
            marker_size=20,  # 20 pixels
            marker_type='circle',  # Circle marker
            filename_suffix='_red_circle'
        )
    
    print(f"Marked image saved to: {marked_image_path}")

if __name__ == "__main__":
    from rich import print
    # 构造输入
    # instruction = "请点击屏幕上的‘会员’按钮"  # 示例指令
    instruction = "请帮我搜索周杰伦的歌"
    image_path = "assets/test.jpeg"  # 你的图片路径
    image = Image.open(image_path).convert("RGB")
    image = __resize__(image)
    image_base64 = encode_image_to_base64(image)

    result = query_ollama(image_base64, instruction)
    print(result)