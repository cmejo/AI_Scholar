#!/bin/bash

# Advanced Models for 2x RTX 3090 (48GB VRAM)
# This script pulls state-of-the-art models that are more advanced than the current Ollama models

echo "🚀 Pulling State-of-the-Art Models for 2x RTX 3090..."
echo "💾 Total VRAM Available: 48GB"
echo ""

# Set Ollama host
export OLLAMA_HOST=http://localhost:11435

echo "📥 1. Pulling Qwen2.5-72B-Instruct (SOTA reasoning model)..."
ollama pull qwen2.5:72b-instruct

echo "📥 2. Pulling Llama-3.1-70B-Instruct (Latest Llama)..."
ollama pull llama3.1:70b-instruct

echo "📥 3. Pulling DeepSeek-Coder-V2-16B (Advanced coding)..."
ollama pull deepseek-coder-v2:16b

echo "📥 4. Pulling Qwen2.5-Math-72B (Mathematical reasoning)..."
ollama pull qwen2.5-math:72b

echo "📥 5. Pulling Qwen2.5-Coder-32B (Advanced coding)..."
ollama pull qwen2.5-coder:32b

echo "📥 6. Pulling Qwen2.5-32B-Instruct (Financial analysis)..."
ollama pull qwen2.5:32b-instruct

echo ""
echo "⚠️  Note: Mixtral 8x22B requires ~45GB VRAM (tight fit)"
echo "📥 7. Pulling Mixtral-8x22B (Optional - Mixture of Experts)..."
read -p "Pull Mixtral 8x22B? It uses almost all your VRAM (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ollama pull mixtral:8x22b
else
    echo "Skipping Mixtral 8x22B"
fi

echo ""
echo "🎉 Advanced model installation complete!"
echo ""
echo "📋 Available models:"
ollama list

echo ""
echo "💡 Recommendations for your use cases:"
echo "🔬 AI Scholar (Research): qwen2.5-math:72b, qwen2.5:72b-instruct"
echo "📈 Quant Scholar (Finance): qwen2.5:32b-instruct, llama3.1:70b-instruct"
echo "💻 Coding Tasks: deepseek-coder-v2:16b, qwen2.5-coder:32b"
echo "🧠 General Reasoning: qwen2.5:72b-instruct, llama3.1:70b-instruct"
echo ""
echo "🚀 Your AI Scholar app now has access to state-of-the-art models!"