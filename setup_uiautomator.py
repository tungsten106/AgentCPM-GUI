"""
UIAutomator Controller Setup Script
==================================

这个脚本用于设置 UIAutomator Controller 的环境，包括安装必要的依赖和初始化 uiautomator2。
"""

import os
import sys
import subprocess
import platform

def print_step(step, message):
    """打印步骤信息"""
    print(f"\n[{step}] {message}")
    print("=" * 50)

def run_command(command):
    """运行命令并返回结果"""
    print(f"执行: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: {e}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False

def check_python():
    """检查 Python 版本"""
    print_step(1, "检查 Python 版本")
    python_version = platform.python_version()
    print(f"Python 版本: {python_version}")
    
    major, minor, _ = map(int, python_version.split('.'))
    if major < 3 or (major == 3 and minor < 8):
        print("警告: 推荐使用 Python 3.8 或更高版本")
        return False
    return True

def install_dependencies():
    """安装依赖项"""
    print_step(2, "安装依赖项")
    
    if not os.path.exists("requirements_uiautomator.txt"):
        print("错误: 找不到 requirements_uiautomator.txt 文件")
        return False
    
    return run_command(f"{sys.executable} -m pip install -r requirements_uiautomator.txt")

def init_uiautomator():
    """初始化 uiautomator2"""
    print_step(3, "初始化 uiautomator2")
    
    # 检查是否已安装 uiautomator2
    try:
        import uiautomator2
        print("uiautomator2 已安装")
    except ImportError:
        print("错误: uiautomator2 未安装，请先安装依赖项")
        return False
    
    # 初始化 uiautomator2
    print("初始化 uiautomator2 (这可能需要几分钟时间)")
    return run_command(f"{sys.executable} -m uiautomator2 init")

def check_device():
    """检查设备连接"""
    print_step(4, "检查设备连接")
    
    try:
        import uiautomator2 as u2
        
        # 获取设备列表
        devices = u2.list_connected_devices()
        if not devices:
            print("警告: 未检测到已连接的设备")
            print("请确保您的设备已连接并启用了 USB 调试")
            print("您可以稍后运行 'python -m uiautomator2 init' 来初始化设备")
            return False
        
        print(f"检测到 {len(devices)} 个设备:")
        for i, device in enumerate(devices):
            print(f"  {i+1}. {device}")
        
        # 尝试连接第一个设备
        device = u2.connect(devices[0])
        print(f"成功连接到设备: {device.info}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def check_model():
    """检查模型文件"""
    print_step(5, "检查模型文件")
    
    model_path = "model/AgentCPM-GUI"
    if not os.path.exists(model_path):
        print(f"警告: 找不到默认模型路径 '{model_path}'")
        print("请确保您已下载 AgentCPM-GUI 模型并放置在正确的位置")
        print("或者在运行时使用 --model 参数指定模型路径")
        return False
    
    print(f"模型路径 '{model_path}' 存在")
    return True

def main():
    """主函数"""
    print("UIAutomator Controller 环境设置")
    print("==============================")
    
    # 检查 Python 版本
    if not check_python():
        print("\n警告: Python 版本检查未通过，但将继续安装")
    
    # 安装依赖项
    if not install_dependencies():
        print("\n错误: 安装依赖项失败")
        return
    
    # 初始化 uiautomator2
    if not init_uiautomator():
        print("\n错误: 初始化 uiautomator2 失败")
        return
    
    # 检查设备连接
    check_device()
    
    # 检查模型文件
    check_model()
    
    print("\n设置完成！")
    print("您现在可以使用以下命令运行 UIAutomator Controller:")
    print("  Windows: run_uiautomator.bat --task \"您的任务\"")
    print("  Linux/macOS: ./run_uiautomator.sh --task \"您的任务\"")
    print("或者直接运行:")
    print("  python uiautomator_controller.py --task \"您的任务\"")

if __name__ == "__main__":
    main()
