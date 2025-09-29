## ollama部署
安装ollama.exe: https://ollama.com/download

## 转换模型为gguf格式
参考： https://github.com/OpenSQZ/MiniCPM-V-CookBook/blob/main/quantization/gguf/minicpm-v4_5_gguf_quantize_zh.md
环境：
```
pip install torch torchvision transformers gguf sentencepiece mistral-common
```

从llama.cpp获取相应的代码，并进入llama.cpp作为working dir
```
git clone  https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
```

### 步骤 1: 对模型结构进行预处理
```
python tools\mtmd\legacy-models\minicpmv-surgery.py -m ../AgentCPM-GUI/model\AgentCPM-GUI
```

### 步骤 2: 将视觉编码器转换为 GGUF 格式
```
python ./tools/mtmd/legacy-models/minicpmv-convert-image-encoder-to-gguf.py -m ../AgentCPM-GUI\model\AgentCPM-GUI --minicpmv-projector ../AgentCPM-GUI\model\AgentCPM-GUI\minicpmv.projector --output-dir ../AgentCPM-GUI/model\AgentCPM-GUI --minicpmv_version 3
```

### 步骤 3: 将语言模型转换为 GGUF 格式
```
python .\convert_hf_to_gguf.py ../AgentCPM-GUI\model\AgentCPM-GUI\model
```

如果出现 `trust_remote_code=True` 的报错，修改convert_hf_to_gguf.py, line 457: 
```python
config = AutoConfig.from_pretrained(dir_model, trust_remote_code=False).to_dict()
```

# ollama创建模型
ollama create agentcpm -f Modelfile

Modelfile内容：
```
FROM model\AgentCPM-GUI\mmproj-model-f16.gguf
FROM model\AgentCPM-GUI\model\Model-7.6B-F16.gguf

TEMPLATE """{{ if .System }}<|im_start|>system
 
{{ .System }}<|im_end|>{{ end }}
 
{{ if .Prompt }}<|im_start|>user
 
{{ .Prompt }}<|im_end|>{{ end }}
 
<|im_start|>assistant<|im_end|>
 
{{ .Response }}<|im_end|>"""
 
PARAMETER stop "<|endoftext|>"
PARAMETER stop "<|im_end|>"
```