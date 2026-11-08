"""Cooperative lock and fail-closed GPU-release checks for the Paint lab."""
import fcntl
import os
from pathlib import Path
import stat

def open_lock(path, capsule_sync):
    path=Path(path)
    if not path.is_absolute() or '..' in path.parts:raise ValueError('absolute lock path required')
    capsule_sync._sans_echappement(path,'verrou')
    capsule_sync._dossier(path.parent,'dossier du verrou',0o700)
    fd=os.open(path,os.O_RDWR|os.O_NOFOLLOW)
    try:
        meta=os.fstat(fd)
        if not stat.S_ISREG(meta.st_mode) or meta.st_uid!=os.getuid() or meta.st_mode&0o077:
            raise ValueError('lock must be a private regular file owned by current user')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return fd
    except BaseException:
        os.close(fd)
        raise

def parse_pids(value):
    result=set()
    for line in value.splitlines():
        value=line.strip()
        if not value:continue
        if not value.isdigit() or int(value)<1:raise ValueError('invalid GPU PID response')
        result.add(int(value))
    return result

def namespace_stopped(result,supervision):
    identity=result.get('identite_namespace')
    if identity is None:return False
    if any(x['etat'] not in ('Z','X') for x in supervision._namespace(identity['ns'])):return False
    for previous in result.get('processus_observés',[]):
        try:current=supervision.identite(previous['pid'])
        except FileNotFoundError:continue
        if supervision._meme(previous,current) and current['etat'] not in ('Z','X'):return False
    return True

def check_release(namespace_clear,gpu_pids):
    """Bounded final check. Other GPU PIDs are reported, never signalled."""
    try:
        complete=bool(namespace_clear())
        current=sorted(gpu_pids())
    except Exception as exc:
        return {'status':'non_verifie','namespace_stopped':False,'gpu_pids':None,'foreign_pids':None,'error':type(exc).__name__}
    return {'status':'verifie' if complete and not current else 'non_verifie',
            'namespace_stopped':complete,'gpu_pids':current,
            'foreign_pids':current if complete else None,'error':None}
