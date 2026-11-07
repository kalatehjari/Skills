#!/usr/bin/env bash
# Install what narrate.py / narrate_cast.py need and download the two models into ./models.
set -e
cd "$(dirname "$0")"
pip install --break-system-packages -q sherpa-onnx soundfile scipy numpy 2>/dev/null || pip3 install -q sherpa-onnx soundfile scipy numpy
command -v ffmpeg >/dev/null || echo "ffmpeg is missing: install it (apt-get install ffmpeg, or brew install ffmpeg on a Mac)"
mkdir -p models && cd models
if [ ! -d kokoro-multi-lang-v1_0 ]; then
  curl -sSL -o kokoro.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_0.tar.bz2
  tar xjf kokoro.tar.bz2 && rm kokoro.tar.bz2
fi
if [ ! -d sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8 ]; then
  curl -sSL -o p.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2
  tar xjf p.tar.bz2 && rm p.tar.bz2
fi
echo "Ready: $(pwd)"
