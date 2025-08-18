# Bark Detector

Advanced YAMNet-based bark detection system with real-time monitoring and comprehensive analysis.

## Requirements

- **Python**: 3.9 - 3.11 (3.11.4 recommended)
- **Platforms**: 
  - Apple Silicon Macs (M1/M2)
  - Intel Macs (x86_64)
  - Linux (x86_64)

## Installation

### Automatic Installation (Recommended)

The `install.py` script automatically detects your platform and installs the correct dependencies:

```bash
uv venv
uv run install.py
```
**Note**: The script creates a platform-specific `pyproject.toml` file that is not tracked in git to prevent conflicts between different architectures.

### Manual Installation

#### Apple Silicon Mac (M1/M2)
```bash
uv add -r requirements-apple-silicon.txt
```

#### Intel Mac / Linux
```bash
uv add -r requirements-intel.txt
```

#### Compatibility Issues
If you encounter dependency conflicts, try the fallback versions:
```bash
uv add -r requirements-fallback.txt
```

## Python Version Management

This project uses Python 3.11.4 (specified in `.python-version`). If you're using pyenv:

```bash
# Install Python 3.11.4 if needed
pyenv install 3.11.4

# Set local Python version
pyenv local 3.11.4

# Verify version
python --version  # Should show Python 3.11.4
```

## Usage

### Basic Monitoring
```bash
# Start monitoring with default settings
uv run python -m bark_detector

# Use custom sensitivity
uv run python -m bark_detector --sensitivity 0.5

# Save to custom directory
uv run python -m bark_detector --output-dir my_recordings
```

### Configuration Files
```bash
# Create a configuration file
uv run python -m bark_detector --create-config config.json

# Use configuration file
uv run python -m bark_detector --config config.json

# Override config file values with CLI
uv run python -m bark_detector --config config.json --sensitivity 0.8
```

### Legacy Usage
```bash
# Legacy entry point (still supported)
uv run bd.py
```

The detector will:
- Load YAMNet ML model on first run
- Monitor audio input in real-time
- Log bark detections with confidence and intensity
- Record audio sessions when barking is detected
- Provide comprehensive analysis of recordings

## Cross-Platform Deployment

### From Apple Silicon Mac to Intel Mac

1. Copy these files to your Intel Mac:
   ```
   bd.py
   install.py
   requirements-intel.txt
   requirements-fallback.txt
   .python-version
   ```

2. On Intel Mac, run:
   ```bash
   python3 install.py
   ```

3. The installer will automatically use Intel-compatible TensorFlow versions.

## Configuration

Default settings in `bd.py`:
- **Sensitivity**: 0.05 (lower = more sensitive)
- **Sample Rate**: 16kHz (YAMNet requirement)
- **Quiet Duration**: 30 seconds before stopping recording
- **Session Gap**: 10 seconds to group barks into sessions

## Calibration

Quick Example:

uv run bd.py --calibrate-files \
   --audio-files samples/bark_sample1.wav samples/bark_sample2.wav samples/background.wav \
   --ground-truth-files bark_sample1_gt.json bark_sample2_gt.json \
   --save-profile kelowna_legal_evidence \
   --sensitivity-range 0.01 0.2 \
   --steps 25

### Complete Calibration Example

Step 1: Create Ground Truth Templates

# Create templates for your existing bark recordings
uv run bd.py --create-template samples/bark_recording_20250729_142441.wav

This creates a JSON template:
{
"audio_file": "samples/bark_recording_20250729_142441.wav",
"duration": 45.2,
"instructions": "Add bark events with start_time and end_time in seconds",
"events": [
{
   "start_time": 5.0,
   "end_time": 7.5,
   "description": "Example: Dog barking - replace with actual timestamps",
   "confidence_expected": 1.0
}
]
}

Step 2: Annotate Ground Truth

Edit the JSON file with actual bark timestamps:
{
"events": [
{
   "start_time": 12.3,
   "end_time": 14.8,
   "description": "First bark session - loud barking"
},
{
   "start_time": 28.5,
   "end_time": 31.2,
   "description": "Second bark session - continuous"
},
{
   "start_time": 41.0,
   "end_time": 43.5,
   "description": "Final bark - medium intensity"
}
]
}

Step 3: Run File-Based Calibration

# Test with multiple files + ground truth
uv run bd.py --calibrate-files \
--audio-files bark1.wav bark2.wav background_noise.wav \
--ground-truth-files bark1_gt.json bark2_gt.json \
--save-profile kelowna_optimized \
--sensitivity-range 0.01 0.3 \
--steps 30

🔬 What Happens During Calibration:

🔍 Running sensitivity sweep: 0.010 to 0.300
📊 Testing 3 files with 30 sensitivity levels
📁 Added test file: bark1.wav (3 ground truth events)
📁 Added test file: bark2.wav (5 ground truth events)
📁 Added test file: background_noise.wav (0 ground truth events)

🎛️ Testing sensitivity 0.010 (1/30)
Precision: 45%, Recall: 95%, F1: 0.612
🎛️ Testing sensitivity 0.020 (2/30)
Precision: 67%, Recall: 89%, F1: 0.766
...
🎛️ Testing sensitivity 0.087 (15/30)
Precision: 89%, Recall: 85%, F1: 0.870  ← Best F1 Score
...

## Usage Examples

### Discover Voice Memo files:
uv run bd.py --list-convertible ~/Downloads

### Record calibration sample:
uv run bd.py --record my_bark_sample.wav

### Use converted files for calibration:
uv run bd.py --calibrate-files --audio-files voice_memo.m4a background.wav

## Troubleshooting

### TensorFlow Installation Issues
- Ensure Python version is 3.9-3.11
- Try fallback installation: `uv add -r requirements-fallback.txt`
- Check platform detection in `install.py`

### Audio Issues
- Verify microphone permissions
- Check PyAudio installation: `python -c "import pyaudio; print('OK')"`
- On macOS, you may need to install PortAudio: `brew install portaudio`

### YAMNet Model Issues
- First run downloads ~200MB model
- Requires internet connection for initial download
- Model cached in `/tmp/tfhub_modules/`

## Files

- `bd.py` - Main bark detector application
- `install.py` - Cross-platform dependency installer
- `requirements-*.txt` - Platform-specific dependencies
- `.python-version` - Python version specification
- `recordings/` - Output directory for audio recordings
- `bark_detector.log` - Application logs

## Misc Notes

iCloud Voice Memos are saved in different folders depending on the OS:

MacOS 14.6.1 Sonoma:
~/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings

MacOS 11.6.1 Big Sur:
~/Library/Application Support/com.apple.voicememos/Recordings