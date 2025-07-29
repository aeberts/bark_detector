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
python3 install.py
```

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

Run the bark detector:
```bash
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

Example:

uv run bd.py --calibrate-files \
   --audio-files recordings/bark_sample1.wav samples/bark_sample2.wav samples/background.wav \
   --ground-truth-files bark_sample1_gt.json bark_sample2_gt.json \
   --save-profile kelowna_legal_evidence \
   --sensitivity-range 0.01 0.2 \
   --steps 25

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