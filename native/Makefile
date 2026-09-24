# ============================================================================
#  X++ v0.4.1 – Native VM (ZCOM / ZITR / ZJIT) build
#  Zero-dependency C++17. Requires only a C++ compiler.
#  Usage:
#     make            -> ../xppvm      (repo root)
#     make PREFIX=~   -> install
#     make clean
# ============================================================================
CXX      ?= g++
CXXFLAGS ?= -O2 -std=c++17 -Wall -Wextra -Wno-unused-parameter
TARGET    = ../xppvm
SRCS      = xpp_main.cpp xpp_parse.cpp xpp_codegen.cpp xpp_vm.cpp xpp_values.cpp xpp_nativegen.cpp

all: $(TARGET)

$(TARGET): $(SRCS) xpp.hpp zjit_runtime.hpp
	$(CXX) $(CXXFLAGS) -o $@ $(SRCS)
	@echo "built: $(TARGET)"

debug:
	$(CXX) -O0 -g -std=c++17 -o ../xppvm $(SRCS)

install: $(TARGET)
	install -m 755 ../xppvm $(DESTDIR)$(PREFIX)/bin/xppvm
	install -m 644 zjit_runtime.hpp $(DESTDIR)$(PREFIX)/share/xpp/zjit_runtime.hpp

clean:
	rm -f ../xppvm

.PHONY: all debug install clean
