// ============================================================================
//  xpp_main.cpp – xppvm CLI: ZCOM (bytecode compiler) / ZITR (VM) / ZJIT (AOT)
//  X++ v0.4.1 – native VM, no Python required to run .xp programs
// ============================================================================
#include "xpp.hpp"
#include <cstdio>
#include <cstring>
#include <fstream>
#include <sstream>
#include <iostream>
#include <chrono>
#include <cstdlib>

namespace xpp {

static std::string dirname_of(const char* argv0) {
    std::string p = argv0 ? argv0 : ".";
    size_t pos = p.find_last_of("/\\");
    if (pos == std::string::npos) return ".";
    if (pos == 0) return "/";
    return p.substr(0, pos);
}

static std::string read_file(const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    if (!f) throw XppError("cannot open " + path);
    std::stringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

static void write_file(const std::string& path, const std::vector<u8>& data) {
    std::ofstream f(path, std::ios::binary);
    if (!f) throw XppError("cannot write " + path);
    f.write((const char*)data.data(), (std::streamsize)data.size());
}

static void usage() {
    fprintf(stderr,
        "xppvm – X++ v0.4.1 native VM (ZCOM / ZITR / ZJIT)\n"
        "\n"
        "  xppvm zcom <file.xp> [-o out.xbc] [--disasm]   ZCOM: compile to bytecode\n"
        "  xppvm zitr <file.xp> [--verbose]               ZITR: run on native VM\n"
        "  xppvm zjit <file.xp> [--verbose] [--keep]      ZJIT: native AOT build+run\n"
        "  xppvm disasm <file.xbc>                        disassemble bytecode\n"
        "  xppvm run <file.xp> [--mode ZCOM|ZITR|ZJIT]\n"
        "  xppvm version\n");
}

int cli_main(int argc, char** argv) {
    if (argc < 2) { usage(); return 1; }
    std::string cmd = argv[1];

    if (cmd == "version" || cmd == "--version" || cmd == "-V") {
        printf("X++ Native VM v0.4.1\n");
        printf("  ZCOM – strict bytecode compiler (AOT)\n");
        printf("  ZITR – stack VM interpreter (bytecode)\n");
        printf("  ZJIT – native AOT backend (X++ -> C++ -> machine code)\n");
        printf("  ITR  – AI intent compiler (via Python x command, RNM=ITR)\n");
        return 0;
    }

    // common helpers
    std::string file, out, mode;
    bool verbose = false, disasm = false, keep = false;
    for (int i = 2; i < argc; i++) {
        std::string a = argv[i];
        if (a == "-o" && i + 1 < argc) out = argv[++i];
        else if (a == "--mode" && i + 1 < argc) mode = argv[++i];
        else if (a == "--disasm" || a == "-d") disasm = true;
        else if (a == "--verbose" || a == "-v") verbose = true;
        else if (a == "--keep") keep = true;
        else if (a == "-h" || a == "--help") { usage(); return 0; }
        else if (!a.empty() && a[0] == '-') { fprintf(stderr, "unknown option: %s\n", a.c_str()); return 2; }
        else file = a;
    }
    if (cmd == "run") cmd = mode.empty() ? "ZITR" : mode;
    for (auto& c : cmd) c = (char)toupper((unsigned char)c);
    if (cmd == "ZITR" || cmd == "XITR" || cmd == "VM") cmd = "ZITR";
    if (cmd == "ZCOM" || cmd == "XCOM") cmd = "ZCOM";
    if (cmd == "ZJIT" || cmd == "NATIVE") cmd = "ZJIT";

    try {
        if (cmd == "ZITR") {
            if (file.empty()) { usage(); return 1; }
            auto t0 = std::chrono::steady_clock::now();
            Module m;
            if (file.size() >= 4 && file.substr(file.size() - 4) == ".xbc") {
                std::vector<u8> data;
                std::ifstream f(file, std::ios::binary);
                if (!f) throw XppError("cannot open " + file);
                data.assign(std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>());
                m = load_module(data.data(), data.size());
            } else {
                std::string src = read_file(file);
                Program prog = parse_program(src);
                m = compile_program(prog);
            }
            auto t1 = std::chrono::steady_clock::now();
            VM vm(m);
            Value r = vm.run({});
            (void)r;
            auto t2 = std::chrono::steady_clock::now();
            if (verbose) {
                double comp = std::chrono::duration<double, std::milli>(t1 - t0).count();
                double run = std::chrono::duration<double, std::milli>(t2 - t1).count();
                fprintf(stderr, "[ZITR] compile %.3f ms | exec %.3f ms\n", comp, run);
            }
            return 0;
        }

        if (cmd == "ZCOM") {
            if (file.empty()) { usage(); return 1; }
            std::string src = read_file(file);
            auto t0 = std::chrono::steady_clock::now();
            Program prog = parse_program(src);
            Module m = compile_program(prog);
            auto t1 = std::chrono::steady_clock::now();
            if (disasm) std::cout << disassemble(m);
            if (out.empty()) {
                size_t dot = file.find_last_of('.');
                out = (dot == std::string::npos ? file : file.substr(0, dot)) + ".xbc";
            }
            std::vector<u8> blob = save_module(m);
            write_file(out, blob);
            if (verbose) {
                double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
                fprintf(stderr, "[ZCOM] %zu functions, %zu globals, %zu constants | %.3f ms -> %s\n",
                        m.funcs.size(), m.globals.size(), m.constants.size(), ms, out.c_str());
            } else {
                printf("ZCOM OK -> %s (%zu bytes bytecode, %zu functions)\n",
                       out.c_str(), blob.size(), m.funcs.size());
            }
            return 0;
        }

        if (cmd == "DISASM") {
            if (file.empty()) { usage(); return 1; }
            std::vector<u8> data;
            std::ifstream f(file, std::ios::binary);
            if (!f) throw XppError("cannot open " + file);
            data.assign(std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>());
            Module m = load_module(data.data(), data.size());
            std::cout << disassemble(m);
            return 0;
        }

        if (cmd == "ZJIT") {
            if (file.empty()) { usage(); return 1; }
            // resolve the directory that contains zjit_runtime.hpp.
            // Prefer the runtime that sits next to THIS binary (setup always
            // installs both together), so stale XPP_NATIVE_DIR env vars or old
            // installed copies can never poison a newer binary. The env var is
            // only a fallback for unusual layouts.
            std::string rtdir;
            std::string d = dirname_of(argc > 0 ? argv[0] : nullptr);
            if (std::ifstream(d + "/zjit_runtime.hpp")) rtdir = d;
            else if (std::ifstream(d + "/native/zjit_runtime.hpp")) rtdir = d + "/native";
            else {
                const char* env = getenv("XPP_NATIVE_DIR");
                if (env && std::ifstream(std::string(env) + "/zjit_runtime.hpp")) rtdir = env;
                else rtdir = d;
            }
            std::string out_exe = file + ".zexe";
            if (keep) {
                std::string err;
                if (!zjit_build(file, out_exe, rtdir, verbose, &err)) {
                    fprintf(stderr, "ZJIT error: %s\n", err.c_str());
                    return 1;
                }
                printf("ZJIT OK -> %s\n", out_exe.c_str());
                return 0;
            }
            // run path: builds once, then reuses the cached native binary
            return zjit_run(file, rtdir, verbose);
        }

        usage();
        return 1;
    } catch (const XppError& e) {
        fprintf(stderr, "X++ [%s] error: %s\n", cmd.c_str(), e.what());
        return 1;
    } catch (const std::exception& e) {
        fprintf(stderr, "X++ [%s] error: %s\n", cmd.c_str(), e.what());
        return 1;
    }
}

} // namespace xpp

int main(int argc, char** argv) {
    return xpp::cli_main(argc, argv);
}
