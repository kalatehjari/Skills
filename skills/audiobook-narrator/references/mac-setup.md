# Running the Python narrator on a Mac

1. Install Python 3.10+ from python.org, and ffmpeg (Homebrew from brew.sh, then `brew install ffmpeg`).
2. `pip3 install sherpa-onnx soundfile scipy numpy`
3. Put `narrate.py`, `narrate_cast.py` and the script in one folder, with a `models` folder inside it.
4. Download and unpack into `models` (about 450 MB; double-click a .tar.bz2 to unpack):
   - https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_0.tar.bz2
   - https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2
5. `cd` into the folder and run
   `python3 narrate_cast.py PE_v8_Ch01_narration_script.txt "Possible Enough v8 - Chapter 01.mp3"`

Or simply `bash setup_env.sh` from the scripts folder, which does steps 2 and 4.

The browser alternative needs no installation: double-click `PE_Narrator.html` in Chrome or Safari (internet needed the first time to download the model).
