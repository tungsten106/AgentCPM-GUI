"""
UIAutomator Controller Example
=============================

这个示例脚本展示了如何使用 uiautomator_controller.py 来控制 Android 设备。
"""

import argparse
import os
from PIL import Image
import time

# 导入控制器类
from uiautomator_controller import UIAutomatorController, AgentCPMController

def run_example(device_id=None, model_path="model/AgentCPM-GUI", device_gpu="cuda:0"):
    """
    运行示例任务
    """
    print("=== UIAutomator Controller Example ===")
    
    # 初始化控制器
    print("初始化 UIAutomator 控制器...")
    ui_controller = UIAutomatorController(device_id)
    
    print("初始化 AgentCPM 控制器...")
    agent_controller = AgentCPMController(model_path, device_gpu)
    
    # 示例任务
    tasks = [
        "打开设置应用",
        "搜索并打开 Wi-Fi 设置",
        "返回主页",
    ]
    
    # 执行任务
    for i, task in enumerate(tasks):
        print(f"\n=== 任务 {i+1}/{len(tasks)}: {task} ===")
        
        # 截取屏幕
        print("截取屏幕...")
        screenshot = ui_controller.take_screenshot()
        
        # 保存当前截图用于演示
        example_dir = "example_screenshots"
        os.makedirs(example_dir, exist_ok=True)
        screenshot_path = os.path.join(example_dir, f"task_{i+1}_before.png")
        screenshot.save(screenshot_path)
        print(f"截图保存至: {screenshot_path}")
        
        # 获取模型动作
        print("分析屏幕并生成操作...")
        action = agent_controller.get_action(screenshot, task)
        
        if not action:
            print("无法获取模型动作，跳过此任务")
            continue
        
        # 执行动作
        print("执行动作...")
        status = ui_controller.execute_action(action)
        
        # 等待UI更新
        time.sleep(2)
        
        # 截取操作后的屏幕
        after_screenshot = ui_controller.take_screenshot()
        after_screenshot_path = os.path.join(example_dir, f"task_{i+1}_after.png")
        after_screenshot.save(after_screenshot_path)
        print(f"操作后截图保存至: {after_screenshot_path}")
        
        print(f"任务状态: {status}")
    
    print("\n=== 示例任务执行完成 ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UIAutomator Controller Example")
    parser.add_argument("--device", type=str, help="Device ID to connect to", default=None)
    parser.add_argument("--model", type=str, help="Path to AgentCPM-GUI model", default="model/AgentCPM-GUI")
    parser.add_argument("--device-gpu", type=str, help="GPU device to use", default="cuda:0")
    args = parser.parse_args()
    
    run_example(args.device, args.model, args.device_gpu)
