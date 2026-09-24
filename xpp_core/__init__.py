"""
X++ v0.4.1
Strict pseudocode compiler + native VM (ZCOM/ZITR/ZJIT) + legacy Python
paths (XCOM/XITR) + AI intent fallback (ITR)
Author: Aagastya Verma / Atom Software
"""
__version__ = "0.4.1"

# native VM modes (v0.4.1)
RNM_ZCOM = "ZCOM"   # strict bytecode AOT compiler (C++/xppvm)
RNM_ZITR = "ZITR"   # native stack VM interpreter
RNM_ZJIT = "ZJIT"   # native AOT backend (X++ -> C++ -> machine code)

# legacy Python-resident modes (preserved)
RNM_XCOM = "XCOM"
RNM_XITR = "XITR"
RNM_ITR  = "ITR"    # AI intent (LLM, needs OPENROUTER_API_KEY)
RNM_AI   = "AI"

__all__ = ["__version__",
           "RNM_ZCOM", "RNM_ZITR", "RNM_ZJIT",
           "RNM_XCOM", "RNM_XITR", "RNM_ITR", "RNM_AI"]
