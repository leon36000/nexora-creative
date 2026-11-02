"""Job queue for one GPU: runs, one after another, the command lines of <queue>.txt (re-read after each job, so lines
can be appended while it runs). Lines already run are listed in <queue>.fait. Usage: python3 file.py queue.txt"""
import subprocess, sys, time
from pathlib import Path

f = Path(sys.argv[1]).resolve()
fait = f.with_suffix(".fait")
ici = Path(__file__).resolve().parents[1]
while True:
    faites = set(fait.read_text().splitlines()) if fait.exists() else set()
    a_faire = [l.strip() for l in f.read_text().splitlines() if l.strip() and not l.startswith("#") and l.strip() not in faites]
    if not a_faire:
        time.sleep(15)
        continue
    l = a_faire[0]
    print(f"=== {time.strftime('%H:%M:%S')} {l}", flush=True)
    subprocess.run(l, shell=True, cwd=ici)
    with open(fait, "a") as o:
        o.write(l + "\n")
