#!/usr/bin/env python3
"""Nexora - micro-benchmark bf16 matmul GPU-bound, journal NVML par seconde. Usage: bench5090.py LIMITE_W DUREE_S"""
import sys, time, json, ctypes, threading, urllib.request
import torch
lim, dur = sys.argv[1], int(sys.argv[2])
N = ctypes.CDLL("libnvidia-ml.so.1"); N.nvmlInit_v2()
h = ctypes.c_void_p(); N.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(h))
def u(fn, *a):
    v = ctypes.c_uint(); getattr(N, fn)(h, *a, ctypes.byref(v)); return v.value
def sample():
    pw = u("nvmlDeviceGetPowerUsage") / 1000
    t = u("nvmlDeviceGetTemperature", 0)
    sm = u("nvmlDeviceGetClockInfo", 1)
    fan = u("nvmlDeviceGetFanSpeed_v2", 0) if True else 0
    r = ctypes.c_ulonglong(); N.nvmlDeviceGetCurrentClocksEventReasons(h, ctypes.byref(r))
    return pw, t, sm, fan, r.value
def busy():
    try:
        q = json.load(urllib.request.urlopen("http://127.0.0.1:18388/queue", timeout=2))
        return bool(q["queue_running"] or q["queue_pending"])
    except Exception:
        return False
a = torch.randn(8192, 8192, device="cuda", dtype=torch.bfloat16)
b = torch.randn(8192, 8192, device="cuda", dtype=torch.bfloat16)
for _ in range(20): a @ b
torch.cuda.synchronize()
stop = False; rows = []
def sampler():
    t0 = time.time()
    while not stop:
        rows.append(sample()); time.sleep(1)
th = threading.Thread(target=sampler); th.start()
warm = time.time() + 10
while time.time() < warm: a @ b
torch.cuda.synchronize(); rows.clear()
t0 = time.time(); n = 0; aborted = False
while time.time() - t0 < dur:
    for _ in range(50): a @ b
    n += 50; torch.cuda.synchronize()
    if n % 1000 == 0 and busy(): aborted = True; break
el = time.time() - t0; stop = True; th.join()
tf = n * 2 * 8192**3 / el / 1e12
avg = lambda i: sum(r[i] for r in rows) / max(1, len(rows))
reasons = {}
for r in rows:
    reasons[r[4]] = reasons.get(r[4], 0) + 1
print(json.dumps({"limit_w": lim, "aborted": aborted, "tflops": round(tf, 1), "s": round(el, 1),
  "power_avg_w": round(avg(0), 1), "power_max_w": round(max(r[0] for r in rows), 1),
  "temp_avg_c": round(avg(1), 1), "temp_max_c": max(r[1] for r in rows),
  "sm_avg_mhz": round(avg(2)), "fan_avg_pct": round(avg(3)), "fan_max_pct": max(r[3] for r in rows),
  "reasons_hex_count": {hex(k): v for k, v in reasons.items()}}))
