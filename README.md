# Voice Dictation Assistant

An AI-powered voice dictation application for Windows that provides real-time speech-to-text conversion with intelligent text enhancement and secure configuration management.

## 🚀 Features

### ✅ **Core Audio Processing**
- **Real-time Audio Capture**: High-quality microphone input with configurable sample rates (8kHz-44.1kHz)
- **Advanced Noise Filtering**: Digital signal processing using scipy for improved speech clarity
- **Audio Level Monitoring**: Real-time silence/speech detection with configurable thresholds
- **Multi-Device Support**: Automatic microphone detection and selection with hot-swapping capability
- **Dual Recording Modes**: Streaming and batch recording with configurable buffer sizes

### ✅ **Speech Recognition Engine**
- **AssemblyAI Integration**: Primary speech-to-text service with real-time streaming API
- **OpenAI Whisper Fallback**: Offline processing for privacy-conscious users
- **Confidence Scoring**: Transcription reliability assessment for each result
- **Custom Vocabulary Support**: Domain-specific terminology and proper noun recognition
- **Caching System**: Avoids re-transcribing identical audio for improved performance
- **Error Recovery**: Automatic retry with exponential backoff for transient failures

### ✅ **AI Text Enhancement**
- **GPT-4o-mini Integration**: Advanced text processing with GPT-3.5-turbo fallback
- **Context-Aware Processing**: Adapts enhancement based on application type (email, document, code, chat)
- **Specialized Enhancement Functions**:
  - Grammar correction and sentence structure improvement
  - Smart punctuation insertion and filler word removal
  - Proper noun capitalization and contraction fixes
  - Technical terminology preservation
- **Customizable Prompt Templates**: User-defined enhancement instructions
- **Token Usage Tracking**: Cost management and API usage monitoring

### ✅ **Smart Text Insertion System**
- **Universal Application Support**: Works with any Windows application
- **Cursor Position Detection**: Accurate cursor tracking using Windows APIs
- **Dual Insertion Methods**: Clipboard-based and direct typing with automatic fallback
- **Application-Specific Formatting**: Smart character replacements and length validation
- **Undo Functionality**: Complete reversal of text insertions
- **Error Recovery**: Robust handling of insertion failures with multiple recovery strategies
- **Special Application Handling**: Support for secure apps, development environments, and terminals

### ✅ **Global Hotkey Management**
- **System-Wide Shortcuts**: Customizable keyboard combinations (default: Ctrl+Win+Space)
- **Push-to-Talk Mode**: Hold to record, release to process with configurable timing
- **Conflict Detection**: Automatic detection of system and application shortcut conflicts
- **Fallback Suggestions**: Smart alternative hotkey recommendations
- **Visual & Audio Feedback**: Immediate feedback for all hotkey actions
- **Windows Security Compliance**: UAC compatibility and permission management

### ✅ **Configuration Management System**
- **Secure Storage**: Windows DPAPI encryption for sensitive data like API keys
- **Multi-Profile Support**: Multiple configuration profiles with isolated settings
- **Structured Schema**: Pydantic-based configuration validation and type safety
- **Setup Wizard**: Interactive first-time configuration with guided API key setup
- **Nested Configuration Access**: Dot-notation support for complex settings
- **Profile Management**: Create, switch, rename, copy, export, and import profiles

### ✅ **Advanced Features**
- **Context-Aware Processing**: 8 predefined contexts (Email, Document, Code, Chat, etc.)
- **Performance Monitoring**: Response time tracking and usage analytics
- **Comprehensive Logging**: Rotating file handlers with detailed error reporting
- **Error Classification**: Categorized error handling with user-friendly messages
- **Resource Management**: Proper cleanup and memory management

### ✅ **Core Application Architecture** (Task 9 Implementation)
- **Application Controller**: Central orchestrator managing all system components
- **Workflow Management**: State-driven workflow orchestration with concurrent processing
- **User Feedback System**: Visual and audio feedback for all user interactions
- **Error Handling & Recovery**: Robust error detection, classification, and automatic recovery strategies
- **Performance Monitoring**: Comprehensive metrics tracking including workflow latency, system resources, and usage statistics
- **Thread-Safe Operations**: Concurrent processing with proper synchronization and resource management

## 🏗️ Project Structure

```
Voice/
├── src/                    # Source code
│   ├── audio/             # Audio capture and processing
│   │   └── capture.py     # AudioCapture class with noise filtering
│   ├── recognition/       # Speech recognition engine
│   │   └── speech_recognition.py  # Multi-service transcription
│   ├── ai_processing/     # AI text enhancement
│   │   ├── text_enhancement.py    # Main AI processor
│   │   ├── enhancement_functions.py # Specialized enhancement functions
│   │   ├── context_processor.py   # Context-aware processing
│   │   ├── prompt_templates.py    # Customizable prompt system
│   │   └── cache_manager.py       # Caching and token tracking
│   ├── text_insertion/    # Text insertion system
│   │   ├── cursor_detection.py    # Cursor position detection
│   │   ├── text_insertion_system.py # Core insertion logic
│   │   ├── text_insertion.py      # Text insertion utilities
│   │   ├── formatting.py          # Application-specific formatting
│   │   ├── error_recovery.py      # Error handling and recovery
│   │   └── special_handling.py    # Special application support
│   ├── hotkeys/          # Global hotkey management
│   │   ├── hotkey_manager.py      # Core hotkey registration
│   │   ├── push_to_talk.py        # Push-to-talk functionality
│   │   ├── conflict_detector.py   # Conflict detection system
│   │   ├── feedback_system.py     # Visual and audio feedback
│   │   └── security_compatibility.py # Windows security compliance
│   ├── config/           # Configuration management
│   │   ├── config_manager.py      # Main configuration system
│   │   ├── schema.py              # Pydantic configuration models
│   │   ├── secure_storage.py      # DPAPI encryption for sensitive data
│   │   ├── profile_manager.py     # Multi-profile support
│   │   └── setup_wizard.py        # Interactive setup wizard
│   ├── context/          # Context awareness system
│   │   ├── application_context.py # Application context detection
│   │   ├── text_formatter.py      # Context-specific text formatting
│   │   ├── ai_enhancement_adapter.py # AI enhancement integration
│   │   └── user_rules_manager.py  # User-defined rules management
│   ├── core/             # Core application architecture
│   │   ├── application_controller.py  # Main application controller
│   │   ├── workflow_manager.py        # Workflow orchestration and state management
│   │   ├── types.py                  # Shared types and enums
│   │   ├── feedback_system.py         # User feedback and notifications
│   │   ├── error_handler.py           # Error detection, classification, and recovery
│   │   └── performance_monitor.py     # Performance tracking and usage analytics
│   └── utils/            # Utility functions
│       └── logger.py     # Logging system
├── tests/                # Comprehensive test suite
├── docs/                 # Documentation
├── resources/            # Static resources
├── run_voice_assistant.py # Main application entry point
└── requirements.txt      # Python dependencies
```

## 📋 Requirements

- **Python 3.10+** (tested with Python 3.12.8)
- **Windows 10/11** with microphone access
- **Internet connection** for AI services (AssemblyAI, OpenAI)
- **Administrative privileges** for global hotkey registration

## 🔧 Installation

### Prerequisites
1. **Python Environment**: Ensure Python 3.10+ is installed
2. **Microphone Access**: Configure microphone permissions in Windows
3. **API Keys**: Obtain API keys for AssemblyAI and OpenAI services

### Setup Instructions
```powershell
# Clone the repository
git clone <repository-url>
cd Voice

# Create virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt

# Test the application (will show setup wizard if no API keys configured)
python run_voice_assistant.py
```

## 🚀 Usage

### First-Time Setup
1. **Run the Application**: Execute `python run_voice_assistant.py`
2. **Configure API Keys**: The setup wizard will guide you through API key configuration
3. **Test Audio**: Verify microphone access and audio capture functionality
4. **Configure Hotkeys**: Set your preferred keyboard shortcuts

### Application Architecture
The core application features a robust, modular architecture:

- **ApplicationController**: Central orchestrator that manages all system components
- **WorkflowManager**: Handles the complete dictation workflow with state management
- **UserFeedbackSystem**: Provides visual and audio feedback for all user interactions
- **ErrorHandler**: Implements comprehensive error detection, classification, and recovery
- **PerformanceMonitor**: Tracks workflow performance, system resources, and usage statistics

The system uses concurrent processing with proper thread synchronization to ensure responsive performance while maintaining data integrity.

### Basic Operation
1. **Activate Dictation**: Press `Ctrl+Win+Space` (default) or your custom hotkey
2. **Speak Clearly**: Dictate your text with natural speech patterns
3. **Release to Process**: The system will transcribe and enhance your speech
4. **Text Insertion**: Enhanced text is automatically inserted at your cursor position

### Advanced Features
- **Push-to-Talk**: Hold the hotkey to record, release to process
- **Multiple Profiles**: Switch between different configuration profiles
- **Context Awareness**: The system adapts formatting based on the active application
- **Undo Support**: Use `Ctrl+Win+Z` to undo the last text insertion

## ⚙️ Configuration

### Configuration Files
- **Location**: `%APPDATA%\VoiceDictationAssistant\config.yaml`
- **Format**: YAML with encrypted sensitive data
- **Profiles**: Multiple configuration profiles supported

### Key Settings
```yaml
# Audio Configuration
audio:
  sample_rate: 16000
  channels: 1
  chunk_size: 1024
  silence_threshold: 0.01

# AI Enhancement
ai:
  model: "gpt-4o-mini"
  remove_fillers: true
  improve_grammar: true
  context_aware: true

# Hotkeys
hotkey:
  primary_hotkey: "ctrl+win+space"
  push_to_talk: true
```

## 🧪 Testing

The project includes comprehensive test suites for all components:

```powershell
# Run all tests
python -m pytest tests/

# Test specific modules
python test_audio_capture.py
python test_config_system.py
```

## 📊 Development Status

### ✅ **Completed Features** (Ready for Testing)
- **Task 1**: Project structure and environment setup ✅
- **Task 2**: Audio capture module with noise filtering ✅
- **Task 3**: Speech recognition with multi-service support ✅
- **Task 4**: AI text enhancement with context awareness ✅
- **Task 5**: Text insertion system with universal application support ✅
- **Task 6**: Global hotkey management with security compliance ✅
- **Task 7**: Configuration management with secure storage ✅
- **Task 8**: Application context awareness ✅
- **Task 9**: Core application controller with comprehensive workflow management ✅

### 🔧 **Recent Fixes** (Latest Updates)
- **Import Structure**: Resolved circular import issues and module organization
- **Application Startup**: Fixed application initialization and component loading
- **Type Safety**: Added proper type hints and shared type definitions
- **Error Handling**: Improved error detection and recovery mechanisms

### 🚀 **Ready for Physical Testing**
The application is now ready for physical testing with the following components fully functional:

- ✅ **Core Architecture**: All modules properly integrated
- ✅ **Dependencies**: All required packages installed and working
- ✅ **Import System**: Circular import issues resolved
- ✅ **Configuration**: Secure storage and setup wizard ready
- ✅ **Workflow Management**: Complete dictation workflow implemented

### 🔄 **Next Steps for Testing**
1. **API Key Configuration**: Set up AssemblyAI and OpenAI API keys
2. **Setup Wizard**: Run the interactive configuration wizard
3. **Audio Testing**: Verify microphone access and audio capture
4. **End-to-End Testing**: Test complete dictation workflow

### 📋 **Pending Features** (Future Development)
- **Task 10**: System tray application with GUI
- **Task 11**: Enhanced error handling and logging system
- **Task 12**: Advanced performance monitoring and analytics
- **Task 13**: User interface improvements and accessibility features

## 🤝 Contributing

This project is currently in active development. Please refer to the development plan and technical specifications for more information about contributing.

### Development Guidelines
- Follow the established project structure
- Add comprehensive tests for new features
- Use type hints and proper documentation
- Ensure Windows compatibility and security compliance

## 📝 License

*License information to be added.*

## 🔗 Dependencies

### Core Dependencies
- **pyaudio==0.2.14**: Audio capture and processing
- **assemblyai==0.17.0**: Speech recognition service
- **openai==1.5.0**: AI text enhancement
- **pywin32==306**: Windows API integration
- **pyautogui==0.9.54**: Text insertion automation
- **pygetwindow==0.0.9**: Window detection
- **pyperclip==1.8.2**: Clipboard operations
- **global-hotkeys==0.1.7**: Global hotkey management
- **pyyaml==6.0.1**: Configuration file handling
- **pydantic==2.5.0**: Configuration validation
- **pytest==7.4.0**: Testing framework
- **scipy>=1.11.0**: Advanced signal processing for noise filtering
- **numpy>=1.24.0**: Numerical operations for audio processing
- **requests>=2.31.0**: HTTP client for API communications

### Built-in Dependencies
- **concurrent.futures**: Thread pool execution
- **threading**: Thread synchronization
- **dataclasses**: Structured data containers
- **typing**: Type hints and annotations

## 🆘 Troubleshooting

### Common Issues
1. **Import Errors**: All import issues have been resolved in the latest version
2. **Hotkey Not Working**: Ensure the application has administrative privileges
3. **Microphone Not Detected**: Check Windows microphone permissions
4. **API Errors**: Verify your API keys are correctly configured
5. **Text Not Inserting**: Check if the target application supports text input

### Log Files
- **Location**: `%APPDATA%\VoiceDictationAssistant\logs\voice_assistant.log`
- **Rotation**: Automatic log rotation with detailed error reporting
- **Level**: Configurable logging levels (DEBUG, INFO, WARNING, ERROR)

### Quick Start Guide
```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python run_voice_assistant.py

# 3. Follow the setup wizard to configure API keys
# 4. Test with a simple dictation
```

### Support
For issues and feature requests, please refer to the project documentation or create an issue in the repository.

## 🎯 **Current Status: Ready for Testing!**

The Voice Dictation Assistant is now ready for physical testing. All core components are implemented and the import issues have been resolved. The application can be started with `python run_voice_assistant.py` and will guide you through the initial setup process. 