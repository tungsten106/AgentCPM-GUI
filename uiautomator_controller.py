"""
UIAutomator Controller with AgentCPM-GUI
=======================================

这个脚本使用 uiautomator2 和 AgentCPM-GUI 模型来自动控制 Android 设备。
通过分析屏幕截图，模型可以理解当前界面并生成相应的操作指令，实现自动化交互。

功能特点:
- 自动截取设备屏幕
- 使用 AgentCPM-GUI 模型分析屏幕内容
- 根据模型输出执行点击、滑动、输入文本等操作
- 支持特殊按键操作（HOME、BACK、ENTER）
- 支持任务状态跟踪和反馈
- 支持多轮对话，保留历史对话上下文

前提条件:
- Python 3.8+
- Android 设备（已启用 USB 调试）或模拟器
- 安装了 AgentCPM-GUI 模型

安装:
1. 安装必要的 Python 包:
   pip install uiautomator2 torch transformers pillow argparse

2. 安装 uiautomator2 的 ATX 应用到设备:
   python -m uiautomator2 init

使用方法:
1. 基本用法:
   python uiautomator_controller.py --task "打开微信并发送一条消息给张三"

2. 高级选项:
   python uiautomator_controller.py --device DEVICE_ID --model /path/to/model --device-gpu cuda:0 --task "打开设置并开启飞行模式" --max-steps 15 --reset-history

参数说明:
- --device: 设备 ID，如果有多个设备连接，需要指定
- --model: AgentCPM-GUI 模型路径，默认为 "model/AgentCPM-GUI"
- --device-gpu: 使用的 GPU 设备，默认为 "cuda:0"
- --task: 要执行的任务指令（必需）
- --max-steps: 最大执行步数，默认为 10
- --reset-history: 重置对话历史，开始新的对话

故障排除:
1. 设备连接问题:
   - 确保设备已正确连接到电脑并启用 USB 调试模式
   - 运行 `adb devices` 检查设备是否被识别
   - 尝试重新初始化 uiautomator2: `python -m uiautomator2 init`
   - 如果连接不稳定，尝试更换 USB 线或端口，关闭设备省电模式

2. 模型相关问题:
   - 确保已下载 AgentCPM-GUI 模型并放置在正确的位置
   - 如果出现内存错误，尝试使用 CPU 进行推理: `--device-gpu cpu`
   - 如果模型解析错误，检查模型版本是否兼容

3. 操作执行问题:
   - 如果点击操作不准确，可能是屏幕分辨率转换问题，检查坐标计算逻辑
   - 如果操作执行太快，可以增加等待时间，修改代码中的 `time.sleep()` 值
   - 对于复杂任务，尝试增加最大步数: `--max-steps 20`
"""

import uiautomator2 as u2
import json
import time
import os
import torch
from PIL import Image
import base64
from io import BytesIO
import argparse
# from transformers import AutoTokenizer, AutoModelForCausalLM
import requests

# 将图片长边缩放至1120以降低计算和显存压力
def resize_image(origin_img):
    resolution = origin_img.size
    w, h = resolution
    max_line_res = 1120
    if max_line_res is not None:
        max_line = max_line_res
        if h > max_line:
            w = int(w * max_line / h)
            h = max_line
        if w > max_line:
            h = int(h * max_line / w)
            w = max_line
    img = origin_img.resize((w, h), resample=Image.Resampling.LANCZOS)
    return img

def encode_image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

class AgentCPMController:
    def __init__(self, model_path="model/AgentCPM-GUI", device="cuda:0"):
        # # 加载模型和分词器
        # print("Loading model from", model_path)
        # self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        # self.model = AutoModelForCausalLM.from_pretrained(
        #     model_path, trust_remote_code=True, torch_dtype=torch.bfloat16
        # )
        # self.model = self.model.to(device)
        
        # 加载 schema
        schema_path = 'eval/utils/schema/schema.json'
        self.action_schema = json.load(open(schema_path, encoding="utf-8"))
        
        # 设置系统提示
        items = list(self.action_schema.items())
        insert_index = 3
        items.insert(insert_index, ("required", ["thought"]))  # 启用 thought 字段
        self.action_schema = dict(items)
        
        self.system_prompt = f'''# Role
你是一名熟悉安卓系统触屏GUI操作的智能体，将根据用户的问题，分析当前界面的GUI元素和布局，生成相应的操作。

# Task
针对用户问题，根据输入的当前屏幕截图，输出下一步的操作。

# Rule
- 以紧凑JSON格式输出
- 输出操作必须遵循Schema约束
- 你可以参考历史对话来理解当前任务的上下文

# Schema
{json.dumps(self.action_schema, indent=None, ensure_ascii=False, separators=(',', ':'))}'''

        # 初始化对话历史
        self.conversation_history = []

    def get_action(self, image, instruction):
        """
        获取模型对当前屏幕的操作建议
        """
        # 调整图像大小
        image = resize_image(image)
        image_base64 = encode_image_to_base64(image)

        # 解析输出
        try:
            # 推理
            outputs = self.query_ollama(image_base64, instruction)
            action_content = outputs['choices'][-1]['message']['content']
            action = json.loads(action_content)
            
            # 更新对话历史
            # 添加用户消息到历史记录
            user_message = {
                "role": "user",
                "content": f"<Question>{instruction}</Question>\n当前屏幕截图：[图片]"
            }
            self.conversation_history.append(user_message)
            
            # 添加助手回复到历史记录
            assistant_message = {
                "role": "assistant",
                "content": action_content
            }
            self.conversation_history.append(assistant_message)
            
            return action
        except Exception as e:
            print("Error parsing model!")
            print(e)
            return None
    
    def query_ollama(self, image_base64, instruction:str):
        url = "http://localhost:11434/v1/chat/completions"
        headers = {
            "Content-Type": "application/json"
        }
        
        # 构建消息列表，包含系统提示和历史对话
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # 添加历史对话（不包含当前请求）
        if self.conversation_history:
            messages.extend(self.conversation_history)
        
        # 添加当前用户消息（包含当前截图）
        current_message = {
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
        }
        messages.append(current_message)
        
        data = {
            "model": "agentcpm:latest",
            "messages": messages,
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
            print(f"Request error: {e}")
            return None

class UIAutomatorController:
    def __init__(self, device_id=None):
        """
        初始化 UIAutomator 控制器
        device_id: 设备ID，如果为None则连接到第一个可用设备
        """
        if device_id:
            self.device = u2.connect(device_id)
        else:
            self.device = u2.connect()
        
        print(f"Connected to device: {self.device.info}")
        
        # 创建输出目录
        self.screenshot_dir = "screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    def take_screenshot(self):
        """
        截取当前屏幕
        """
        screenshot_path = os.path.join(self.screenshot_dir, f"screen_{int(time.time())}.png")
        self.device.screenshot(screenshot_path)
        return Image.open(screenshot_path)
    
    def execute_action(self, action):
        """
        执行模型输出的动作
        """
        print(f"Executing action: {json.dumps(action, ensure_ascii=False)}")
        
        # 打印思考过程
        if "thought" in action:
            print(f"Thought: {action['thought']}")
        
        # 点击操作
        if "POINT" in action:
            x, y = action["POINT"]
            # 将0-1000的坐标转换为实际屏幕坐标
            screen_width, screen_height = self.device.window_size()
            actual_x = int(x * screen_width / 1000)
            actual_y = int(y * screen_height / 1000)
            
            # 检查是否有滑动操作
            if "to" in action:
                to_value = action["to"]
                duration = action.get("duration", 200)
                
                if isinstance(to_value, list):  # 如果是坐标
                    end_x, end_y = to_value
                    actual_end_x = int(end_x * screen_width / 1000)
                    actual_end_y = int(end_y * screen_height / 1000)
                    print(f"Swiping from ({actual_x}, {actual_y}) to ({actual_end_x}, {actual_end_y})")
                    self.device.swipe(actual_x, actual_y, actual_end_x, actual_end_y, duration/1000.0)
                else:  # 如果是方向
                    swipe_distance = min(screen_width, screen_height) // 3
                    if to_value == "up":
                        self.device.swipe(actual_x, actual_y, actual_x, actual_y - swipe_distance, duration/1000.0)
                    elif to_value == "down":
                        self.device.swipe(actual_x, actual_y, actual_x, actual_y + swipe_distance, duration/1000.0)
                    elif to_value == "left":
                        self.device.swipe(actual_x, actual_y, actual_x - swipe_distance, actual_y, duration/1000.0)
                    elif to_value == "right":
                        self.device.swipe(actual_x, actual_y, actual_x + swipe_distance, actual_y, duration/1000.0)
            else:
                # 普通点击或长按
                duration = action.get("duration", 200)
                if duration > 200:  # 长按
                    print(f"Long pressing at ({actual_x}, {actual_y}) for {duration}ms")
                    self.device.long_click(actual_x, actual_y, duration/1000.0)
                else:  # 普通点击
                    print(f"Clicking at ({actual_x}, {actual_y})")
                    self.device.click(actual_x, actual_y)
        
        # 特殊按键操作
        elif "PRESS" in action:
            button = action["PRESS"]
            if button == "HOME":
                print("Pressing HOME button")
                self.device.press("home")
            elif button == "BACK":
                print("Pressing BACK button")
                self.device.press("back")
            elif button == "ENTER":
                print("Pressing ENTER button")
                self.device.press("enter")
        
        # 文本输入操作
        elif "TYPE" in action:
            text = action["TYPE"]
            print(f"Typing text: {text}")
            self.device.send_keys(text)
        
        # 检查任务状态
        status = action.get("STATUS", "continue")
        return status

def main():
    parser = argparse.ArgumentParser(description="UIAutomator controller with AgentCPM-GUI")
    parser.add_argument("--device", type=str, help="Device ID to connect to", default=None)
    parser.add_argument("--model", type=str, help="Path to AgentCPM-GUI model", default="model/AgentCPM-GUI")
    parser.add_argument("--device-gpu", type=str, help="GPU device to use", default="cuda:0")
    parser.add_argument("--task", type=str, help="Task instruction", required=True)
    parser.add_argument("--max-steps", type=int, help="Maximum number of steps", default=10)
    parser.add_argument("--reset-history", action="store_true", help="Reset conversation history")
    args = parser.parse_args()
    
    # 初始化控制器
    ui_controller = UIAutomatorController(args.device)
    agent_controller = AgentCPMController(args.model, args.device_gpu)
    
    # 如果指定了重置历史，则清空历史记录
    if args.reset_history:
        agent_controller.conversation_history = []
        print("Conversation history has been reset.")
    
    # 执行任务
    instruction = args.task
    step_count = 0
    status = "continue"
    
    print(f"Starting task: {instruction}")
    
    while status == "continue" and step_count < args.max_steps:
        step_count += 1
        print(f"\nStep {step_count}:")
        
        # 截取屏幕
        screenshot = ui_controller.take_screenshot()
        
        # 获取模型动作
        action = agent_controller.get_action(screenshot, instruction)
        if not action:
            print("Failed to get action from model")
            break
        
        # 执行动作
        status = ui_controller.execute_action(action)
        
        # 等待UI更新
        time.sleep(1)
        
        # 检查任务状态
        if status == "finish":
            print("Task completed successfully!")
            break
        elif status == "satisfied":
            print("Task already satisfied!")
            break
        elif status == "impossible":
            print("Task is impossible to complete!")
            break
        elif status == "interrupt":
            print("Task interrupted!")
            break
        elif status == "need_feedback":
            feedback = input("Task needs feedback. Please provide feedback: ")
            instruction = f"{instruction} (Feedback: {feedback})"
    
    if step_count >= args.max_steps:
        print(f"Reached maximum number of steps ({args.max_steps})")
    
    print("Task execution finished")
    
    # 打印对话历史长度
    print(f"Conversation history length: {len(agent_controller.conversation_history)} messages")
    
    # 询问是否要保存对话历史
    save_history = input("Do you want to save the conversation history? (y/n): ")
    if save_history.lower() == 'y':
        history_file = f"conversation_history_{int(time.time())}.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(agent_controller.conversation_history, f, ensure_ascii=False, indent=2)
        print(f"Conversation history saved to {history_file}")

if __name__ == "__main__":
    main()
