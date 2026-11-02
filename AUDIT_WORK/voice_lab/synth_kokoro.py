import sys, time, json, resource, soundfile as sf
from kokoro_onnx import Kokoro
model, voices, voice, out, text = sys.argv[1:6]
t0 = time.time(); k = Kokoro(model, voices); t_load = time.time() - t0
t1 = time.time(); samples, sr = k.create(text, voice=voice, speed=1.0, lang="hi"); t_syn = time.time() - t1
sf.write(out, samples, sr)
dur = len(samples) / sr
print(json.dumps({"voice": voice, "sr": sr, "audio_sec": round(dur, 3), "load_sec": round(t_load, 2), "synth_sec": round(t_syn, 2), "rtf": round(t_syn / dur, 3), "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)}))
