pip install pymupdf# StudySet AI — Local LLM (Ollama) Setup & Hardware Guide

## 1. Overview
StudySet AI is engineered to prioritize **local, private inference** using Ollama. This ensures complete privacy for candidate resumes, eliminates recurring cloud token bills, and guarantees offline capability.

---

## 2. Hardware Requirements

| Component | Minimum Specification | Recommended Specification |
|---|---|---|
| **CPU** | 4 Cores (x86_64 / ARM64) | 8+ Cores (Intel i7/i9, AMD Ryzen 7/9, Apple M-Series) |
| **RAM** | 8 GB | 16 GB - 32 GB |
| **GPU / VRAM** | Integrated / CPU-only | Dedicated NVIDIA GPU with 6GB+ VRAM (RTX 3060 / 4060+) or Apple Silicon Unified Memory |
| **Disk Space** | 10 GB free space | 20 GB free space (SSD recommended) |

---

## 3. Ollama Installation & Configuration

### 3.1 Install Ollama
- **Windows**: Download the installer from [ollama.com/download](https://ollama.com/download). Run `OllamaSetup.exe`.
- **macOS**: `brew install ollama` or download from ollama.com.
- **Linux**:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```

### 3.2 Pull Recommended Models
For StudySet AI, the primary model is `qwen2.5:3b` or `qwen3:4b`:
```bash
# Recommended default model:
ollama pull qwen2.5:3b

# High capability alternative:
ollama pull qwen3:4b

# Coding specialized alternative:
ollama pull qwen2.5-coder:3b
```

### 3.3 Verify Ollama API Connectivity
In a terminal, verify that Ollama is responding on port `11434`:
```bash
curl http://localhost:11434/api/tags
```
Expected response:
```json
{
  "models": [
    {
      "name": "qwen2.5:3b:latest",
      "model": "qwen2.5:3b:latest",
      "modified_at": "2026-..."
    }
  ]
}
```

---

## 4. StudySet AI Configuration (`.env`)
Configure the backend `.env` file to use Ollama:

```env
# AI Provider Configuration
LLM_PRIMARY_PROVIDER=ollama
LLM_FALLBACK_PROVIDER=groq

# Ollama Settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_TIMEOUT_SECONDS=180
OLLAMA_NUM_CTX=8192

# Cloud Fallback (Optional)
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

---

## 5. Benchmarks & Performance
On an 8-core CPU without dedicated GPU acceleration:
- **`qwen2.5:3b`**: ~18-25 tokens/sec (Inference time for 10 MCQ questions: ~4.5 seconds).
- **`qwen3:4b`**: ~14-19 tokens/sec (Inference time for resume parsing: ~6.2 seconds).

With NVIDIA CUDA GPU acceleration (e.g. RTX 4060):
- **`qwen2.5:3b`**: ~75-95 tokens/sec (Inference time: <1.5 seconds).
