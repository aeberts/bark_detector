# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based bark detector project that uses audio processing to detect barking sounds. The project is designed to run on a Raspberry Pi and uses sounddevice and numpy libraries for audio processing.

## Development Setup

Install dependencies:
```bash
uv add -r requirements.txt
```
## Deployment

- python source is synched to the execution environment via git
- github repo: https://github.com/aeberts/bark_detector.git

## Architecture

- `bd.py`: Main bark detection script (currently empty - implementation needed)
- `requirements.txt`: Python dependencies (sounddevice, numpy)
- `prd.md`: Product requirements document

## Key Dependencies

- `pyaudio`: For audio input/output (Pi-compatible)
- `numpy`: For numerical processing of audio data

The project is designed for real-time audio processing and detection on embedded hardware.