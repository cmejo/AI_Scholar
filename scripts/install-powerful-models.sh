#!/bin/bash
# Install powerful models optimized for dual RTX 3090 (48GB VRAM total)

echo "🚀 Installing Powerful Models for Dual RTX 3090 Setup"
echo "Total VRAM: 48GB (24GB per card)"
echo "============================================================"

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    ollama serve &
    sleep 5
fi

# Function to pull model with progress
pull_model() {
    local model=$1
    local description=$2
    echo ""
    echo "📥 Pulling $model"
    echo "   $description"
    echo "   This may take several minutes..."
    ollama pull "$model"
    if [ $? -eq 0 ]; then
        echo "✅ Successfully installed $model"
    else
        echo "❌ Failed to install $model"
    fi
}

# Large Language Models (70B+ parameters)
echo ""
echo "🧠 Installing Large Language Models (70B+ parameters)"
echo "These models will utilize most of your 48GB VRAM"

pull_model "llama3.1:70b" "Meta Llama 3.1 70B - Most capable general model (~40GB)"
pull_model "qwen2.5:72b" "Alibaba Qwen 2.5 72B - Excellent reasoning and coding (~42GB)"
pull_model "mixtral:8x7b" "Mistral Mixtral 8x7B - Mixture of Experts model (~26GB)"

# Specialized Large Models
echo ""
echo "🔬 Installing Specialized Large Models"

pull_model "codellama:70b" "Meta CodeLlama 70B - Advanced code generation (~40GB)"
pull_model "wizardlm2:70b" "WizardLM2 70B - Enhanced reasoning capabilities (~40GB)"
pull_model "solar:10.7b" "Upstage Solar 10.7B - Efficient high-performance model (~7GB)"

# Medium Models (Good for parallel processing)
echo ""
echo "⚡ Installing Medium Models (Efficient for parallel processing)"

pull_model "llama3.1:8b" "Meta Llama 3.1 8B - Fast and efficient (~5GB)"
pull_model "qwen2.5:14b" "Alibaba Qwen 2.5 14B - Balanced performance (~9GB)"
pull_model "gemma2:27b" "Google Gemma 2 27B - Research-optimized (~16GB)"
pull_model "phi3:14b" "Microsoft Phi-3 14B - Efficient reasoning (~9GB)"

# Specialized Models
echo ""
echo "🎯 Installing Specialized Models"

pull_model "deepseek-coder:33b" "DeepSeek Coder 33B - Advanced code understanding (~20GB)"
pull_model "mathstral:7b" "Mistral Mathstral 7B - Mathematics specialist (~4GB)"
pull_model "llava:34b" "LLaVA 34B - Vision-language model (~20GB)"

# Quantized Large Models (More efficient)
echo ""
echo "📊 Installing Quantized Large Models (Memory efficient)"

pull_model "llama3.1:70b-instruct-q4_0" "Llama 3.1 70B Quantized - Reduced memory usage (~35GB)"
pull_model "qwen2.5:72b-instruct-q4_0" "Qwen 2.5 72B Quantized - Efficient large model (~36GB)"

# Function to test model
test_model() {
    local model=$1
    echo "Testing $model..."
    response=$(ollama run "$model" "Hello, can you tell me about quantum computing in one sentence?" --timeout 30s 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        echo "✅ $model is working"
    else
        echo "⚠️  $model may need more time to load"
    fi
}

# Test a few models
echo ""
echo "🧪 Testing installed models..."
test_model "llama3.1:8b"
test_model "qwen2.5:14b"

# Show installed models
echo ""
echo "📋 Installed Models Summary:"
ollama list

echo ""
echo "🎉 Installation Complete!"
echo ""
echo "💡 Usage Tips for Dual RTX 3090:"
echo "• Large models (70B+): Use one at a time for maximum performance"
echo "• Medium models (8-27B): Can run multiple simultaneously"
echo "• For scientific work: Try qwen2.5:72b or llama3.1:70b"
echo "• For coding: Use codellama:70b or deepseek-coder:33b"
echo "• For math: Use mathstral:7b"
echo ""
echo "🔧 Model Selection in AI Scholar:"
echo "• The models will appear in your dropdown menu"
echo "• Larger models provide better quality but slower responses"
echo "• Choose based on your task complexity and speed requirements"
echo ""
echo "⚡ Performance Optimization:"
echo "• Monitor GPU memory: nvidia-smi"
echo "• Use quantized models for better memory efficiency"
echo "• Consider running multiple smaller models for parallel processing"