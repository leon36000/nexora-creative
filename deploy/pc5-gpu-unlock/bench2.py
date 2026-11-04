import sys, time, subprocess, threading, json, ctypes, torch
cb = None
for n in ("libcublas.so.12","libcublas.so.13","libcublas.so"):
    try: cb = ctypes.CDLL(n); break
    except OSError: pass
if cb is None:
    import glob,os,nvidia
    p = glob.glob(os.path.dirname(nvidia.__path__[0]+"/")+"/cublas/lib/libcublas.so*")
    cb = ctypes.CDLL(p[0])
def smi(i):
    o = subprocess.check_output(["nvidia-smi","-i",str(i),"--query-gpu=power.draw,temperature.gpu,clocks.sm","--format=csv,noheader,nounits"]).decode().split(",")
    return [float(x) for x in o]
CUDA_R_16F=2; CUBLAS_COMPUTE_16F=64; CUBLAS_COMPUTE_32F=68; GEMM_DEFAULT_TENSOR_OP=99
def gemm(h,a,b,c,n,comp,one):
    return cb.cublasGemmEx(h,0,0,n,n,n,ctypes.byref(one),ctypes.c_void_p(b.data_ptr()),CUDA_R_16F,n,ctypes.c_void_p(a.data_ptr()),CUDA_R_16F,n,ctypes.byref(zero_for(comp)),ctypes.c_void_p(c.data_ptr()),CUDA_R_16F,n,comp,GEMM_DEFAULT_TENSOR_OP)
_z={}
def zero_for(comp):
    return _z[comp]
def timed(f,secs=6):
    for _ in range(3): f()
    torch.cuda.synchronize(); t0=time.time(); it=0
    while time.time()-t0<secs:
        for _ in range(10): f()
        it+=10
    torch.cuda.synchronize(); return it/(time.time()-t0)
def run(i):
    torch.cuda.set_device(i); d=f"cuda:{i}"
    h=ctypes.c_void_p(); cb.cublasCreate_v2(ctypes.byref(h))
    n=8192
    a=(torch.randn(n,n,device=d)*0.1).half(); b=(torch.randn(n,n,device=d)*0.1).half(); c=torch.empty_like(a)
    samples=[]; stop=[False]
    def poll():
        while not stop[0]: samples.append(smi(i)); time.sleep(0.5)
    t=threading.Thread(target=poll); t.start()
    r=dict(gpu=i,name=torch.cuda.get_device_name(i))
    one32=ctypes.c_float(1.0); _z[CUBLAS_COMPUTE_32F]=ctypes.c_float(0.0)
    r["fp16_acc32_tflops"]=round(2*n**3*timed(lambda: gemm(h,a,b,c,n,CUBLAS_COMPUTE_32F,one32))/1e12,1)
    one16=ctypes.c_uint16(0x3c00); _z[CUBLAS_COMPUTE_16F]=ctypes.c_uint16(0)
    r["fp16_acc16_tflops"]=round(2*n**3*timed(lambda: gemm(h,a,b,c,n,CUBLAS_COMPUTE_16F,one16))/1e12,1)
    ai=torch.randint(-8,8,(n,n),device=d,dtype=torch.int8); bi=torch.randint(-8,8,(n,n),device=d,dtype=torch.int8)
    try: r["int8_tops"]=round(2*n**3*timed(lambda: torch._int_mm(ai,bi))/1e12,1)
    except Exception as e: r["int8_tops"]=str(e)[:60]
    a32=torch.randn(4096,4096,device=d); torch.backends.cuda.matmul.allow_tf32=False
    r["fp32_tflops"]=round(2*4096**3*timed(lambda: a32@a32,3)/1e12,1)
    x=torch.empty(512*1024*1024//4*2,device=d); y=torch.empty_like(x)
    torch.cuda.synchronize(); t1=time.time()
    for _ in range(50): y.copy_(x)
    torch.cuda.synchronize(); r["mem_GBps"]=round(2*x.numel()*4*50/(time.time()-t1)/1e9)
    stop[0]=True; t.join(); s=samples[2:] or samples
    r.update(power_W=round(sum(x[0] for x in s)/len(s),1),temp_C=max(x[1] for x in s),sm_MHz=round(sum(x[2] for x in s)/len(s)))
    print(json.dumps(r),flush=True)
for i in map(int,sys.argv[1:] or range(torch.cuda.device_count())): run(i)
