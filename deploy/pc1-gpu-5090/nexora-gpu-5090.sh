#!/usr/bin/python3
# Nexora : RTX 5090 de pc1, plafond de puissance + ventilateur au maximum.
# Propriétaire : Nexora. Usage : préserver la carte (puissance réduite, refroidissement permanent).
# Créé le 03/11/2026. Voir docs/RESSOURCES.md (registre pc1) et docs/ENVIRONNEMENTS.md.
# Modes : apply (démarrage), watch (minuterie, ré-applique si le pilote a réinitialisé), revert (retour aux valeurs d'origine).
# Aucune dépendance : NVML par ctypes. Journal : journald (tag nexora-gpu-5090).
import ctypes, sys, syslog

CONF = "/etc/default/nexora-gpu-5090"
HARD_MIN_W, HARD_MAX_W = 400, 600      # bornes de sécurité absolues
TEMP_FALLBACK_C = 83                    # au-dessus, si le ventilateur ne répond pas : retour au mode automatique
FAN_PCT = 100
syslog.openlog("nexora-gpu-5090")

def log(msg, prio=syslog.LOG_INFO):
    syslog.syslog(prio, msg); print(msg, flush=True)

def conf():
    c = {"POWER_LIMIT_W": "475", "FAN_PERCENT": str(FAN_PCT)}
    try:
        for ln in open(CONF):
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1); c[k.strip()] = v.strip()
    except OSError:
        pass
    return c

N = ctypes.CDLL("libnvidia-ml.so.1")
def chk(rc, what):
    if rc != 0:
        raise RuntimeError("%s a échoué (code NVML %d)" % (what, rc))
if N.nvmlInit_v2() != 0:
    log("NVML indisponible", syslog.LOG_ERR); sys.exit(1)
H = ctypes.c_void_p(); chk(N.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(H)), "handle GPU")

def getu(fn, *a):
    v = ctypes.c_uint(); rc = getattr(N, fn)(H, *a, ctypes.byref(v)); return v.value if rc == 0 else None

def fan_auto():
    n = ctypes.c_uint(); N.nvmlDeviceGetNumFans(H, ctypes.byref(n))
    for i in range(n.value):
        N.nvmlDeviceSetDefaultFanSpeed_v2(H, i)
        N.nvmlDeviceSetFanControlPolicy(H, i, 0)   # 0 = température (automatique)

def revert():
    fan_auto()
    N.nvmlDeviceSetPowerManagementLimit(H, ctypes.c_uint(HARD_MAX_W * 1000))
    log("retour aux valeurs d'origine : ventilateur automatique, plafond %d W" % HARD_MAX_W)

def apply(watch):
    c = conf()
    try: want_w = max(HARD_MIN_W, min(HARD_MAX_W, int(c["POWER_LIMIT_W"])))
    except ValueError: want_w = 475
    try: pct = max(30, min(100, int(c["FAN_PERCENT"])))
    except ValueError: pct = FAN_PCT
    n = ctypes.c_uint(); chk(N.nvmlDeviceGetNumFans(H, ctypes.byref(n)), "nombre de ventilateurs")
    # persistance
    pm = ctypes.c_uint()
    if N.nvmlDeviceGetPersistenceMode(H, ctypes.byref(pm)) == 0 and pm.value != 1:
        N.nvmlDeviceSetPersistenceMode(H, 1)
    # plafond de puissance (en mW)
    cur = getu("nvmlDeviceGetPowerManagementLimit")
    if cur is None or cur != want_w * 1000:
        chk(N.nvmlDeviceSetPowerManagementLimit(H, ctypes.c_uint(want_w * 1000)), "plafond de puissance")
        log("plafond de puissance réglé à %d W (avant : %s)" % (want_w, "?" if cur is None else cur // 1000))
    # ventilateur
    temp = getu("nvmlDeviceGetTemperature", 0)
    if temp is None:
        fan_auto(); log("température illisible : ventilateur remis en automatique", syslog.LOG_WARNING); return 2
    bad = False
    for i in range(n.value):
        pol = getu("nvmlDeviceGetFanControlPolicy_v2", i)  # signature (h, fan, *policy)
        tgt = getu("nvmlDeviceGetTargetFanSpeed", i)
        spd = getu("nvmlDeviceGetFanSpeed_v2", i)
        if pol != 1 or tgt != pct:
            if N.nvmlDeviceSetFanControlPolicy(H, i, 1) != 0 or N.nvmlDeviceSetFanSpeed_v2(H, i, pct) != 0:
                fan_auto(); log("réglage du ventilateur %d refusé : retour en automatique" % i, syslog.LOG_ERR); return 3
            log("ventilateur %d en manuel à %d %% (policy=%s cible=%s)" % (i, pct, pol, tgt))
        spd = getu("nvmlDeviceGetFanSpeed_v2", i)
        if temp >= TEMP_FALLBACK_C and (spd is None or spd < 20):
            bad = True
    if bad:
        fan_auto(); log("GPU à %d °C et ventilateur sans réponse : retour en automatique" % temp, syslog.LOG_CRIT); return 4
    if watch is False:
        log("appliqué : %d W, ventilateur %d %%, %d °C, vitesse lue %s %%" % (want_w, pct, temp, spd))
    return 0

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    try:
        if mode == "revert": revert(); rc = 0
        elif mode in ("apply", "watch"): rc = apply(mode == "watch")
        else: print("usage : %s apply|watch|revert" % sys.argv[0]); rc = 64
    except Exception as e:
        log("erreur : %s ; ventilateur remis en automatique" % e, syslog.LOG_ERR)
        try: fan_auto()
        except Exception: pass
        rc = 1
    sys.exit(rc)
