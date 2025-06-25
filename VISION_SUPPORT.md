# Multimodal AI Vision Support

This document describes the multimodal AI vision support feature that allows users to upload images and ask questions about them.

## Overview

The vision support feature transforms AI Scholar into a powerful analytical tool by enabling:
- Image upload and analysis
- Visual question answering
- Chart and diagram interpretation
- Handwritten note recognition
- Photo analysis and description

## Supported Models

The following vision-capable models are supported:
- **LLaVA** (llava, llava-llama3, llava-phi3, llava-v1.6)
- **BakLLaVA** (bakllava)
- **MoonDream** (moondream)
- **CogVLM** (cogvlm)
- **Qwen-VL** (qwen-vl)

## Installation

### 1. Install a Vision Model

First, install a vision-capable model using Ollama:

```bash
# Install LLaVA (recommended)
ollama pull llava

# Or install other vision models
ollama pull llava-llama3
ollama pull bakllava
ollama pull moondream
```

### 2. Database Migration

Run the database migration to add image support:

```bash
# If using Alembic
alembic upgrade head

# Or manually update your database schema
python -c "
from app import app, db
with app.app_context():
    db.create_all()
"
```

## Usage

### Frontend Usage

1. **Select a Vision Model**: Choose a vision-capable model from the model selector
2. **Upload Images**: Click the image icon (📷) in the chat input to upload images
3. **Ask Questions**: Type your question about the images or leave blank for general description
4. **Send**: The AI will analyze the images and provide detailed responses

### API Usage

#### Upload Images via REST API

```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What do you see in this image?",
    "model": "llava",
    "images": ["data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="]
  }'
```

#### Response Format

```json
{
  "success": true,
  "response": "I can see a red square with a blue rectangle in the center...",
  "model": "llava",
  "session_id": 123,
  "timestamp": "2024-01-15T10:30:00Z",
  "vision_used": true
}
```

## Features

### Image Upload
- **Multiple Images**: Upload up to 5 images per message
- **Format Support**: PNG, JPEG, GIF, WebP
- **Size Limit**: 10MB per image
- **Preview**: See thumbnails before sending

### Image Display
- **Thumbnail View**: Images shown as thumbnails in chat
- **Full-Size Modal**: Click images to view full size
- **Image Metadata**: File name and size information

### Vision Analysis
- **Automatic Detection**: System detects if selected model supports vision
- **Smart Prompting**: Default prompts for image-only messages
- **Error Handling**: Clear error messages for unsupported models

## Technical Implementation

### Backend Changes

1. **Database Schema**: Added `has_images` and `images` fields to `ChatMessage` model
2. **API Endpoints**: Enhanced `/api/chat` to handle image data
3. **Ollama Integration**: Updated service to pass images to vision models
4. **Model Detection**: Added vision model detection logic

### Frontend Changes

1. **Image Upload**: File input with drag-and-drop support
2. **Image Preview**: Thumbnail display with remove functionality
3. **Model Awareness**: UI adapts based on selected model capabilities
4. **Message Display**: Enhanced message component to show images

### Data Flow

1. User selects images in frontend
2. Images converted to base64 data URLs
3. Sent to backend with message text
4. Backend validates model supports vision
5. Images passed to Ollama API
6. Response includes vision analysis
7. Frontend displays result with image context

## Configuration

### Environment Variables

```bash
# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llava

# Image upload limits
MAX_IMAGES_PER_MESSAGE=5
MAX_IMAGE_SIZE_MB=10
```

### Model Configuration

Vision models can be configured with specific parameters:

```python
# Example model parameters for LLaVA
model_params = {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 512
}
```

## Troubleshooting

### Common Issues

1. **"Model does not support vision"**
   - Solution: Install and select a vision-capable model

2. **"Image too large"**
   - Solution: Resize images to under 10MB

3. **"No response from vision model"**
   - Solution: Check Ollama service is running and model is loaded

### Testing

Run the test script to verify vision support:

```bash
python test_vision_support.py
```

### Debugging

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger('services.ollama_service').setLevel(logging.DEBUG)
```

## Examples

### Use Cases

1. **Chart Analysis**: "What trends do you see in this graph?"
2. **Document OCR**: "Extract the text from this document"
3. **Photo Description**: "Describe what's happening in this photo"
4. **Diagram Explanation**: "Explain how this circuit works"
5. **Handwriting Recognition**: "What does this handwritten note say?"

### Sample Prompts

- "Analyze this chart and summarize the key insights"
- "What architectural style is shown in this building?"
- "Identify the objects in this image"
- "Extract all text from this screenshot"
- "What mathematical concepts are illustrated here?"

## Security Considerations

- Images are processed in memory and not permanently stored
- Base64 encoding ensures safe transport
- File type validation prevents malicious uploads
- Size limits prevent resource exhaustion
- User authentication required for all vision requests

## Performance

- **Image Processing**: Handled by Ollama vision models
- **Memory Usage**: Images loaded temporarily during processing
- **Response Time**: Varies by model and image complexity (typically 5-30 seconds)
- **Concurrent Requests**: Limited by Ollama service capacity

## Future Enhancements

- **Image Storage**: Optional persistent image storage
- **Batch Processing**: Multiple image analysis in parallel
- **Advanced OCR**: Specialized text extraction models
- **Image Generation**: Integration with image generation models
- **Video Support**: Frame extraction and analysis