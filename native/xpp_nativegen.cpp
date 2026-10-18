// ============================================================================
//  xpp_nativegen.cpp – ZJIT: native AOT code generation (X++ -> C++ -> exe)
//  X++ v0.4.1. Generated programs include zjit_runtime.hpp and need only
//  libc / libstdc++ at runtime.
// ============================================================================
#include "xpp.hpp"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <map>
#include <set>
#include <iomanip>
#include <filesystem>

namespace xpp {

// Bump whenever the OUTPUT SEMANTICS of generated C++ change; cached .zexe
// binaries are rebuilt when this no longer matches their sidecar stamp.
#define XPP_ZJIT_STAMP "z3"

namespace {

std::string cpp_escape(const std::string& s) {
    std::string o;
    for (char c : s) {
        switch (c) {
            case '\\': o += "\\\\"; break;
            case '"': o += "\\\""; break;
            case '\n': o += "\\n"; break;
            case '\t': o += "\\t"; break;
            case '\r': o += "\\r"; break;
            default: o += c;
        }
    }
    return o;
}

struct Gen {
    std::ostringstream& os;
    std::map<std::string, u32> func_idx;

    explicit Gen(std::ostringstream& o) : os(o) {}

    static std::string gname(const std::string& n) { return "p_g_" + n; }
    static std::string lname(const std::string& n) { return "p_l_" + n; }
    static std::string fname(const std::string& n) { return "p_f_" + n; }

    void collect_locals(const std::vector<Stmt>& body, std::set<std::string>& out) const {
        for (auto& st : body) collect_in_stmt(st, out);
    }
    void collect_in_stmt(const Stmt& st, std::set<std::string>& out) const {
        switch (st.k) {
            case Stmt::SET_: out.insert(st.name); break;
            case Stmt::LOOPF_: case Stmt::LOOPX_: out.insert(st.name); break;
            case Stmt::SAFE_: if (st.has_exc) out.insert(st.exc); break;
            default: break;
        }
        if (st.k == Stmt::IF_) {
            for (auto& arm : st.arms) collect_locals(arm.second, out);
            collect_locals(st.els, out);
        } else if (st.k == Stmt::WHILE_ || st.k == Stmt::LOOPF_ || st.k == Stmt::LOOPX_) {
            collect_locals(st.body, out);
        } else if (st.k == Stmt::SAFE_) {
            collect_locals(st.body, out);
            collect_locals(st.els, out);
        }
    }

    void collect_globals(const std::vector<Stmt>& body, std::set<std::string>& out) const {
        for (auto& st : body) {
            if (st.k == Stmt::FN_) continue;
            switch (st.k) {
                case Stmt::SET_: out.insert(st.name); break;
                case Stmt::PUSH_: out.insert(st.name); break;
                case Stmt::LOOPF_: case Stmt::LOOPX_: out.insert(st.name); break;
                default: break;
            }
            if (st.k == Stmt::IF_) {
                for (auto& arm : st.arms) collect_globals(arm.second, out);
                collect_globals(st.els, out);
            } else if (st.k == Stmt::WHILE_ || st.k == Stmt::LOOPF_ || st.k == Stmt::LOOPX_) {
                collect_globals(st.body, out);
            } else if (st.k == Stmt::SAFE_) {
                if (st.has_exc) out.insert(st.exc);
                collect_globals(st.body, out);
                collect_globals(st.els, out);
            }
        }
    }
};

void gen_expr(const Gen& g, std::ostringstream& os, const Expr& e,
              const std::set<std::string>& locals, const std::set<std::string>& params) {
    auto ref = [&](const std::string& n) -> std::string {
        if (params.count(n)) return n;
        if (locals.count(n)) return Gen::lname(n);
        return Gen::gname(n);
    };
    switch (e.k) {
        case Expr::NIL: os << "zj::mk_nil()"; break;
        case Expr::TRUE_: os << "zj::mk_true()"; break;
        case Expr::FALSE_: os << "zj::mk_false()"; break;
        case Expr::INT_: os << "zj::mk_int((std::int64_t)" << e.ival << "LL)"; break;
        case Expr::FLOAT_: os << "zj::mk_float(" << std::setprecision(17) << e.fval << ")"; break;
        case Expr::STR_: os << "zj::mk_str2(\"" << cpp_escape(e.sval) << "\")"; break;
        case Expr::VAR_: os << ref(e.sval); break;
        case Expr::LIST_: {
            os << "zj::mk_list({";
            for (size_t i = 0; i < e.items.size(); i++) { if (i) os << ", "; gen_expr(g, os, e.items[i], locals, params); }
            os << "})";
            break;
        }
        case Expr::DICT_: {
            os << "zj::mk_dict({";
            for (size_t i = 0; i + 1 < e.items.size(); i += 2) {
                if (i) os << ", ";
                os << "{\"" << cpp_escape(e.items[i].sval) << "\", ";
                gen_expr(g, os, e.items[i + 1], locals, params);
                os << "}";
            }
            os << "})";
            break;
        }
        case Expr::CALL_: {
            if (g.func_idx.count(e.sval)) {
                os << Gen::fname(e.sval) << "(";
                for (size_t i = 0; i < e.items.size(); i++) { if (i) os << ", "; gen_expr(g, os, e.items[i], locals, params); }
                os << ")";
            } else {
                os << "zj::builtin(" << builtin_id(e.sval) << ", {";
                for (size_t i = 0; i < e.items.size(); i++) { if (i) os << ", "; gen_expr(g, os, e.items[i], locals, params); }
                os << "})";
            }
            break;
        }
        case Expr::IDX_:
            os << "zj::get(";
            gen_expr(g, os, *e.a, locals, params);
            os << ", ";
            gen_expr(g, os, *e.b, locals, params);
            os << ")";
            break;
        case Expr::ATTR_:
            os << "zj::attr_get(";
            gen_expr(g, os, *e.a, locals, params);
            os << ", \"" << cpp_escape(e.sval) << "\")";
            break;
        case Expr::BIN_: {
            if (e.binop == B_AND || e.binop == B_OR) {
                // AND: if a falsy -> a; else b.   OR: if a truthy -> a; else b.
                os << "([&]{ zj::V _a = ";
                gen_expr(g, os, *e.a, locals, params);
                os << "; if (" << (e.binop == B_AND ? "!" : "") << "_a.truthy()) return _a; return ";
                gen_expr(g, os, *e.b, locals, params);
                os << "; }())";
                break;
            }
            const char* fn = e.binop == B_ADD ? "add" : e.binop == B_SUB ? "sub" : e.binop == B_MUL ? "mul" :
                             e.binop == B_DIV ? "div" : e.binop == B_MOD ? "mod" : e.binop == B_POW ? "pow" :
                             e.binop == B_EQ ? "eq" : e.binop == B_NE ? "ne" : e.binop == B_LT ? "lt" :
                             e.binop == B_LE ? "le" : e.binop == B_GT ? "gt" : "ge";
            os << "zj::" << fn << "(";
            gen_expr(g, os, *e.a, locals, params);
            os << ", ";
            gen_expr(g, os, *e.b, locals, params);
            os << ")";
            break;
        }
        case Expr::NEG_: os << "zj::neg("; gen_expr(g, os, *e.a, locals, params); os << ")"; break;
        case Expr::NOT_: os << "zj::not_("; gen_expr(g, os, *e.a, locals, params); os << ")"; break;
        case Expr::INPUT_: os << "zj::input(\"" << cpp_escape(e.sval) << "\")"; break;
        case Expr::READ_: os << "zj::readf(\"" << cpp_escape(e.sval) << "\")"; break;
        case Expr::LEN_: os << "zj::mk_int(zj::len("; gen_expr(g, os, *e.a, locals, params); os << "))"; break;
    }
}

void gen_stmt(Gen& g, std::ostringstream& os, const Stmt& s,
              const std::set<std::string>& locals, const std::set<std::string>& params, int indent) {
    std::string pad((size_t)indent * 4, ' ');
    auto ref = [&](const std::string& n) -> std::string {
        if (params.count(n)) return n;
        if (locals.count(n)) return Gen::lname(n);
        return Gen::gname(n);
    };
    switch (s.k) {
        case Stmt::EXPR_: os << pad << "(void)("; gen_expr(g, os, s.a, locals, params); os << ");\n"; break;
        case Stmt::SET_:
            if (s.idx.k == Expr::NIL && s.idx.sval.empty()) {
                os << pad << ref(s.name) << " = ";
                gen_expr(g, os, s.a, locals, params);
                os << ";\n";
            } else if (s.idx.k == Expr::ATTR_) {
                os << pad << "zj::attr_set(" << ref(s.name) << ", \"" << cpp_escape(s.idx.sval) << "\", ";
                gen_expr(g, os, s.a, locals, params);
                os << ");\n";
            } else {
                os << pad << "zj::setidx(" << ref(s.name) << ", ";
                gen_expr(g, os, s.idx, locals, params);
                os << ", ";
                gen_expr(g, os, s.a, locals, params);
                os << ");\n";
            }
            break;
        case Stmt::OUT_:
            os << pad << "zj::print(";
            for (size_t i = 0; i < s.args.size(); i++) { if (i) os << ", "; gen_expr(g, os, s.args[i], locals, params); }
            os << ");\n";
            break;
        case Stmt::PUSH_:
            os << pad << "zj::push(" << ref(s.name) << ", ";
            gen_expr(g, os, s.a, locals, params);
            os << ");\n";
            break;
        case Stmt::RET_: os << pad << "return "; gen_expr(g, os, s.a, locals, params); os << ";\n"; break;
        case Stmt::IF_: {
            for (size_t i = 0; i < s.arms.size(); i++) {
                os << pad << (i == 0 ? "if (" : "else if (");
                os << "zj::truthy(";
                gen_expr(g, os, s.arms[i].first, locals, params);
                os << ")) {\n";
                for (auto& st : s.arms[i].second) gen_stmt(g, os, st, locals, params, indent + 1);
                os << pad << "}";
                if (i + 1 < s.arms.size()) os << " ";
            }
            if (!s.els.empty()) {
                if (!s.arms.empty()) os << " ";
                os << "else {\n";
                for (auto& st : s.els) gen_stmt(g, os, st, locals, params, indent + 1);
                os << pad << "}";
            }
            os << "\n";
            break;
        }
        case Stmt::WHILE_: {
            os << pad << "while (zj::truthy(";
            gen_expr(g, os, s.a, locals, params);
            os << ")) {\n";
            for (auto& st : s.body) gen_stmt(g, os, st, locals, params, indent + 1);
            os << pad << "}\n";
            break;
        }
        case Stmt::LOOPF_: {
            std::string var = ref(s.name);
            os << pad << "{\n";
            os << pad << "  " << var << " = "; gen_expr(g, os, s.a, locals, params); os << ";\n";
            os << pad << "  zj::V _end = "; gen_expr(g, os, s.b, locals, params); os << ";\n";
            os << pad << "  zj::V _step = ";
            if (s.step.k == Expr::NIL) os << "zj::mk_int(1)";
            else gen_expr(g, os, s.step, locals, params);
            os << ";\n";
            os << pad << "  for (; zj::truthy(zj::truthy(zj::ge(_step, zj::mk_int(0))) ? zj::le(" << var << ", _end) : zj::ge(" << var << ", _end)); "
               << var << " = zj::add(" << var << ", _step)) {\n";
            for (auto& st : s.body) gen_stmt(g, os, st, locals, params, indent + 2);
            os << pad << "  }\n";
            os << pad << "}\n";
            break;
        }
        case Stmt::LOOPX_: {
            std::string var = ref(s.name);
            os << pad << "{\n";
            os << pad << "  zj::V _seq = "; gen_expr(g, os, s.b, locals, params); os << ";\n";
            os << pad << "  std::int64_t _n = zj::len(_seq);\n";
            os << pad << "  for (std::int64_t _i = 0; _i < _n; _i++) {\n";
            os << pad << "    " << var << " = zj::get(_seq, zj::mk_int(_i));\n";
            for (auto& st : s.body) gen_stmt(g, os, st, locals, params, indent + 2);
            os << pad << "  }\n";
            os << pad << "}\n";
            break;
        }
        case Stmt::SAFE_: {
            os << pad << "try {\n";
            for (auto& st : s.body) gen_stmt(g, os, st, locals, params, indent + 1);
            os << pad << "} catch (zj::Error& _e) {\n";
            os << pad << "  zj::V _err = zj::mk_str2(_e.what());\n";
            if (s.has_exc) os << pad << "  " << ref(s.exc) << " = _err;\n";
            for (auto& st : s.els) gen_stmt(g, os, st, locals, params, indent + 1);
            os << pad << "}\n";
            break;
        }
        case Stmt::BREAK_: os << pad << "break;\n"; break;
        case Stmt::CONT_: os << pad << "continue;\n"; break;
        default: break;
    }
}

bool find_compiler(std::string* out) {
    const char* cands[] = {"g++", "clang++", "c++"};
    for (const char* c : cands) {
        std::string cmd = std::string("command -v ") + c + " >/dev/null 2>&1";
        if (std::system(cmd.c_str()) == 0) { *out = c; return true; }
    }
    return false;
}

} // anonymous namespace

// ---------------------------------------------------------------------------
bool zjit_available() { return true; }

static std::string fnv1a64(const std::string& s) {
    u64 h = 1469598103934665603ULL;
    for (unsigned char c : s) { h ^= c; h *= 1099511628211ULL; }
    char buf[24];
    std::snprintf(buf, sizeof(buf), "%016llx", (unsigned long long)h);
    return buf;
}

bool zjit_build(const std::string& src_path, const std::string& out_exe,
                const std::string& runtime_dir, bool verbose, std::string* err) {
    if (err) err->clear();
    std::ifstream in(src_path);
    if (!in) { if (err) *err = "cannot read " + src_path; return false; }
    std::stringstream ss;
    ss << in.rdbuf();
    std::string src = ss.str();

    Program prog;
    try { prog = parse_program(src); }
    catch (const XppError& e) { if (err) *err = e.what(); return false; }

    // embed the self-contained runtime directly (no copied header to go stale)
    std::ifstream rt(runtime_dir + "/zjit_runtime.hpp");
    if (!rt) { if (err) *err = "runtime header not found: " + runtime_dir + "/zjit_runtime.hpp"; return false; }
    std::stringstream rts; rts << rt.rdbuf();

    std::ostringstream out;
    Gen g(out);
    for (auto& f : prog.funcs) g.func_idx[f.name] = (u32)(&f - &prog.funcs[0]);

    std::set<std::string> globals;
    g.collect_globals(prog.stmts, globals);

    out << rts.str();                 // runtime (has include guard)
    out << "namespace {\n";
    for (const auto& gv : globals) out << "zj::V " << g.gname(gv) << ";\n";
    out << "zj::V p_g_ARGS;\n";
    out << "}\n";

    for (const auto& f : prog.funcs) {
        out << "static zj::V " << g.fname(f.name) << "(";
        for (size_t i = 0; i < f.params.size(); i++) { if (i) out << ", "; out << "const zj::V& " << f.params[i]; }
        out << ");\n";
    }
    for (const auto& f : prog.funcs) {
        std::set<std::string> locals;
        g.collect_locals(f.body, locals);
        std::set<std::string> params(f.params.begin(), f.params.end());
        for (const auto& p : params) locals.erase(p);
        out << "\nstatic zj::V " << g.fname(f.name) << "(";
        for (size_t i = 0; i < f.params.size(); i++) { if (i) out << ", "; out << "const zj::V& " << f.params[i]; }
        out << ") {\n";
        for (const auto& l : locals) out << "  zj::V " << g.lname(l) << ";\n";
        for (auto& st : f.body) gen_stmt(g, out, st, locals, params, 1);
        out << "  return zj::mk_nil();\n}\n";
    }

    out << "\nint main(int argc, char** argv) {\n";
    out << "  p_g_ARGS = zj::mk_list({});\n";
    out << "  try {\n";
    std::set<std::string> none;
    for (auto& st : prog.stmts) {
        if (st.k == Stmt::FN_) continue;
        gen_stmt(g, out, st, none, none, 2);
    }
    out << "  } catch (zj::Error& _e) { std::cerr << \"X++ error: \" << _e.what() << \"\\n\"; return 1; }\n";
    out << "  return 0;\n}\n";

    std::filesystem::path exe(out_exe);
    std::filesystem::path tmpdir = exe.parent_path().empty() ? std::filesystem::path(".") : exe.parent_path();
    std::filesystem::path tmp = tmpdir / (exe.filename().string() + ".src.cpp");

    {
        std::ofstream f(tmp);
        f << out.str();
        if (!f) { if (err) *err = "cannot write temporary source"; return false; }
    }
    std::string cc;
    if (!find_compiler(&cc)) {
        if (err) *err = "no C++ compiler found (install g++ or clang++)";
        std::remove(tmp.c_str());
        return false;
    }
    std::string cmd = cc + " -O2 -std=c++17 -w \"" + tmp.string() + "\" -o \"" + out_exe + "\"";
    if (verbose) fprintf(stderr, "[ZJIT] %s\n", cmd.c_str());
    int rc = std::system(cmd.c_str());
    if (getenv("XPP_ZJIT_KEEP_SRC") == nullptr) std::remove(tmp.c_str());
    if (rc != 0) {
        if (err) *err = "native compile failed (is a C++ compiler installed?)";
        return false;
    }
    // sidecar stamp: invalidates the cache when the generator or runtime change
    {
        std::ofstream sf(out_exe + ".stamp");
        sf << XPP_ZJIT_STAMP << "\n" << fnv1a64(rts.str()) << "\n";
    }
    return true;
}

// A cached binary is fresh only when:
//   * its sidecar stamp matches the current generator stamp AND runtime hash,
//   * the source file is not newer than the binary.
static bool zjit_cache_fresh(const std::string& src_path, const std::string& out_exe,
                             const std::string& runtime_dir) {
    try {
        std::ifstream rt(runtime_dir + "/zjit_runtime.hpp");
        if (!rt) return false;
        std::stringstream rts; rts << rt.rdbuf();
        std::string want = std::string(XPP_ZJIT_STAMP) + "\n" + fnv1a64(rts.str()) + "\n";

        std::ifstream sf(out_exe + ".stamp");
        std::string have((std::istreambuf_iterator<char>(sf)), std::istreambuf_iterator<char>());
        if (!sf || have != want) return false;

        std::error_code ec;
        auto src_t = std::filesystem::last_write_time(src_path, ec);
        if (ec) return false;
        ec.clear();
        auto exe_t = std::filesystem::last_write_time(out_exe, ec);
        if (ec) return false;
        return exe_t >= src_t;
    } catch (...) { return false; }
}

int zjit_run(const std::string& src_path, const std::string& runtime_dir, bool verbose) {
    std::string out_exe = src_path + ".zexe";
    bool fresh = zjit_cache_fresh(src_path, out_exe, runtime_dir);

    if (!fresh) {
        std::string err;
        if (!zjit_build(src_path, out_exe, runtime_dir, verbose, &err)) {
            fprintf(stderr, "ZJIT error: %s\n", err.c_str());
            return 1;
        }
        if (verbose) fprintf(stderr, "[ZJIT] built cached native binary: %s\n", out_exe.c_str());
    } else if (verbose) {
        fprintf(stderr, "[ZJIT] cache hit: %s\n", out_exe.c_str());
    }
    return std::system(out_exe.c_str());
}

} // namespace xpp
