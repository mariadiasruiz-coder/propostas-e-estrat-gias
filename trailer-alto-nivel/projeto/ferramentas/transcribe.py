import json, sys
from faster_whisper import WhisperModel
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
import soundfile as sf, numpy as np
audio,_=sf.read(sys.argv[1], dtype="float32")
segs, info = m.transcribe(audio, language="pt", word_timestamps=True, beam_size=5, vad_filter=False, condition_on_previous_text=False)
out=[]
for s in segs:
    out.append({"start":s.start,"end":s.end,"text":s.text,"words":[{"w":w.word,"s":w.start,"e":w.end} for w in s.words]})
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}", flush=True)
json.dump(out, open(sys.argv[2],"w"), ensure_ascii=False, indent=1)
