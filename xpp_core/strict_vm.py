from .strict_compiler import xcom_compile
import time
_cache={}; _stats={"hits":0,"miss":0,"compile_ms":0.0}
def xitr_run(src: str, strict_ast: bool=False, cache_key=None):
    k = cache_key if cache_key is not None else hash(src)
    code = _cache.get(k)
    if code is not None: _stats["hits"]+=1
    else:
        _stats["miss"]+=1; t0=time.perf_counter()
        code,_ = xcom_compile(src, strict_ast=strict_ast)
        _stats["compile_ms"] += (time.perf_counter()-t0)*1000
        _cache[k]=code
    g={"__builtins__":__builtins__,"__name__":"__main__"}
    exec(code,g); return g
def cache_info(): return dict(_stats, size=len(_cache))
def clear_cache():
    _cache.clear(); _stats.update(hits=0, miss=0, compile_ms=0.0)
