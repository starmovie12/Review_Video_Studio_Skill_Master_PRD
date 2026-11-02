#!/usr/bin/env python3
"""audio_probe: objective voice measurements (module M1). Usage: audio_probe.py file.wav [...]
Prints JSON lines: integrated LUFS, LRA, true peak (ffmpeg ebur128 peak=true), sample rate,
clipped samples (|x| >= 0.999 FS), silence ratio (20 ms frames < -50 dBFS), spectral shares
(<250 Hz, 250-4k, 4-12k) and sibilance band (5-9 kHz) energy share. Needs ffmpeg + numpy."""
import json, re, subprocess, sys
import numpy as np


def ebur128(path):
    p = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True, timeout=300)
    tail = p.stderr[p.stderr.rfind('Summary:'):]
    g = lambda pat: float(re.search(pat, tail).group(1))
    return {'I_LUFS': g(r'I:\s+(-?[\d.]+) LUFS'), 'LRA_LU': g(r'LRA:\s+(-?[\d.]+) LU'), 'TP_dBTP': g(r'Peak:\s+(-?[\d.]+) dBFS')}


def pcm(path):
    info = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries',
                                    'stream=sample_rate,channels', '-of', 'csv=p=0', path]).decode().strip().split(',')
    sr, ch = int(info[0]), int(info[1])
    # average channels explicitly (ffmpeg's default -ac 1 downmix adds +3 dB for correlated L/R)
    pan = 'pan=mono|c0=c0' if ch == 1 else 'pan=mono|c0=0.5*c0+0.5*c1'
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-af', pan, '-f', 'f32le', '-acodec', 'pcm_f32le', '-'],
                       capture_output=True, timeout=300)
    return np.frombuffer(p.stdout, dtype=np.float32), sr


def measure(path):
    out = {'file': path}
    out.update(ebur128(path))
    x, sr = pcm(path)
    out['sr'] = sr
    out['dur_s'] = round(len(x) / sr, 3)
    out['clipped_samples'] = int(np.sum(np.abs(x) >= 0.999))
    fl = int(0.02 * sr)
    n = len(x) // fl
    frames = x[:n * fl].reshape(n, fl)
    rms_db = 20 * np.log10(np.sqrt(np.mean(frames ** 2, axis=1)) + 1e-12)
    out['silence_ratio'] = round(float(np.mean(rms_db < -50)), 3)
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    f = np.fft.rfftfreq(len(x), 1 / sr)
    tot = spec[(f >= 20) & (f <= min(12000, sr / 2))].sum() + 1e-20
    band = lambda a, b: round(float(spec[(f >= a) & (f < b)].sum() / tot), 4)
    out.update({'share_lt250': band(20, 250), 'share_250_4k': band(250, 4000), 'share_4k_12k': band(4000, 12000),
                'sibilance_5_9k': band(5000, 9000)})
    return out


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(json.dumps(measure(p)))
