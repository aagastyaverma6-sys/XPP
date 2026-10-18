// ============================================================================
//  xpp_codegen.cpp – ZCOM: AST -> bytecode compiler, .xbc serializer,
//                     disassembler
//  X++ v0.4.1 – native VM core (zero dependencies)
// ============================================================================
#include "xpp.hpp"
#include <unordered_map>
#include <cstring>
#include <sstream>
#include <cstdio>

namespace xpp {

namespace {

// ---------------------------------------------------------------------------
// Bytecode emitter (all fixups are relative, i32, from the end of the operand)
// ---------------------------------------------------------------------------
struct Code {
    Module* mod;
    Function* fn;
    Code(Module* m, Function* f) : mod(m), fn(f) {}

    size_t here() const { return fn->code.size(); }
    void emit(u8 op) { fn->code.push_back(op); }
    void emit_u32(u32 v) { for (int i = 0; i < 4; i++) fn->code.push_back((u8)((v >> (8 * i)) & 0xFF)); }
    void emit_op(u8 op, u32 arg) { emit(op); emit_u32(arg); }

    // reserve an i32 fixup slot; returns absolute position of the slot
    size_t fixup32() { size_t at = here(); emit_u32(0); return at; }
    void patch(size_t at, size_t target) { patch_rel(at, target, 4); }
    void patch_rel(size_t at, size_t target, size_t width) {
        i32 off = (i32)(target - (at + width));
        for (int i = 0; i < 4; i++) fn->code[at + i] = (u8)((u32)off >> (8 * i));
    }
};

// ---------------------------------------------------------------------------
// Compiler
// ---------------------------------------------------------------------------
struct Compiler {
    Module& mod;
    std::unordered_map<std::string, u32> funcs;
    std::unordered_map<std::string, u32> globals;
    std::unordered_map<std::string, u32> attrs;
    std::unordered_map<std::string, u32> string_idx;
    std::unordered_map<u64, u32> const_idx;

    explicit Compiler(Module& m) : mod(m) {}

    u32 strc(const std::string& s) {
        auto it = string_idx.find(s);
        if (it != string_idx.end()) return it->second;
        u32 i = (u32)mod.strings.size();
        mod.strings.push_back(s);
        string_idx[s] = i;
        return i;
    }
    u32 constc(const Value& v) {
        auto it = const_idx.find(v.bits);
        if (it != const_idx.end()) return it->second;
        u32 i = (u32)mod.constants.size();
        mod.constants.push_back(v);
        const_idx[v.bits] = i;
        return i;
    }
    u32 intc(i64 v) { return constc(Value::integer(v)); }
    u32 floatc(double v) { return constc(Value::real(v)); }
    u32 strv(const std::string& s) { return constc(Value::str((Obj*)(uintptr_t)strc(s))); }
    u32 glob(const std::string& n) {
        auto it = globals.find(n);
        if (it != globals.end()) return it->second;
        u32 i = (u32)mod.globals.size();
        mod.globals.push_back(n);
        globals[n] = i;
        return i;
    }
    u32 attr(const std::string& n) {
        auto it = attrs.find(n);
        if (it != attrs.end()) return it->second;
        u32 i = (u32)mod.attr_names.size();
        mod.attr_names.push_back(n);
        attrs[n] = i;
        return i;
    }

    // ---- scope ------------------------------------------------------------
    struct FuncScope {
        Function* fn;
        std::unordered_map<std::string, u32> locals;
        u32 nlocals = 0;
        std::vector<size_t> breaks, conts;
        bool top = false;
    };
    FuncScope* scope = nullptr;

    u32 local(const std::string& n) {
        auto it = scope->locals.find(n);
        if (it != scope->locals.end()) return it->second;
        u32 i = scope->nlocals++;
        scope->locals[n] = i;
        return i;
    }

    // pre-collect every name assigned inside a function body (Python-like
    // scoping: assignment anywhere makes a name local to the function)
    static void collect_assigns(const std::vector<Stmt>& body, std::vector<std::string>& out) {
        for (auto& st : body) {
            switch (st.k) {
                case Stmt::SET_: out.push_back(st.name); break;
                case Stmt::LOOPF_: case Stmt::LOOPX_: out.push_back(st.name); break;
                case Stmt::SAFE_: if (st.has_exc) out.push_back(st.exc); break;
                default: break;
            }
            if (st.k == Stmt::IF_) {
                for (auto& arm : st.arms) collect_assigns(arm.second, out);
                collect_assigns(st.els, out);
            } else if (st.k == Stmt::WHILE_ || st.k == Stmt::LOOPF_ || st.k == Stmt::LOOPX_) {
                collect_assigns(st.body, out);
            } else if (st.k == Stmt::SAFE_) {
                collect_assigns(st.body, out);
                collect_assigns(st.els, out);
            }
        }
    }

    // ---- expressions ------------------------------------------------------
    void compile_expr(const Expr& e, Code& c) {
        switch (e.k) {
            case Expr::NIL:    c.emit(OP_NULL); break;
            case Expr::TRUE_:  c.emit(OP_TRUE); break;
            case Expr::FALSE_: c.emit(OP_FALSE); break;
            case Expr::INT_:   c.emit_op(OP_CONST_U, intc(e.ival)); break;
            case Expr::FLOAT_: c.emit_op(OP_CONST_U, floatc(e.fval)); break;
            case Expr::STR_:   c.emit_op(OP_CONST_U, strv(e.sval)); break;
            case Expr::VAR_:   load_var(e.sval, c); break;
            case Expr::LIST_: {
                for (auto& it : e.items) compile_expr(it, c);
                c.emit_op(OP_MAKELIST_U, (u32)e.items.size());
                break;
            }
            case Expr::DICT_: {
                for (auto& it : e.items) compile_expr(it, c);
                c.emit_op(OP_MAKEDICT_U, (u32)(e.items.size() / 2));
                break;
            }
            case Expr::CALL_: {
                load_var(e.sval, c);
                for (auto& a : e.items) compile_expr(a, c);
                c.emit_op(OP_CALL_U, (u32)e.items.size());
                break;
            }
            case Expr::IDX_:
                compile_expr(*e.a, c);
                compile_expr(*e.b, c);
                c.emit(OP_IDX);
                break;
            case Expr::ATTR_:
                compile_expr(*e.a, c);
                c.emit_op(OP_ATTR_U, attr(e.sval));
                break;
            case Expr::BIN_: compile_bin(e, c); break;
            case Expr::NEG_: compile_expr(*e.a, c); c.emit(OP_NEG); break;
            case Expr::NOT_: compile_expr(*e.a, c); c.emit(OP_NOT); break;
            case Expr::INPUT_: {
                c.emit_op(OP_BUILTINV_U, builtin_id("input"));
                if (!e.sval.empty()) {
                    c.emit_op(OP_CONST_U, strv(e.sval));
                    c.emit_op(OP_CALL_U, 1);
                } else {
                    c.emit_op(OP_CALL_U, 0);
                }
                break;
            }
            case Expr::READ_: {
                c.emit_op(OP_BUILTINV_U, builtin_id("read"));
                c.emit_op(OP_CONST_U, strv(e.sval));
                c.emit_op(OP_CALL_U, 1);
                break;
            }
            case Expr::LEN_: {
                c.emit_op(OP_BUILTINV_U, builtin_id("len"));
                compile_expr(*e.a, c);
                c.emit_op(OP_CALL_U, 1);
                break;
            }
        }
    }

    void load_var(const std::string& n, Code& c) {
        if (scope && !scope->top) {
            auto it = scope->locals.find(n);
            if (it != scope->locals.end()) { c.emit_op(OP_LOCAL_U, it->second); return; }
        }
        auto f = funcs.find(n);
        if (f != funcs.end()) { c.emit_op(OP_FUNC_U, f->second); return; }
        u32 b = builtin_id(n);
        if (b != 0xFFFFFFFFu) { c.emit_op(OP_BUILTINV_U, b); return; }
        c.emit_op(OP_GLOBAL_U, glob(n));
    }

    void load_lvalue(const std::string& n, Code& c) {
        if (scope && !scope->top) {
            auto it = scope->locals.find(n);
            if (it != scope->locals.end()) { c.emit_op(OP_LOCAL_U, it->second); return; }
        }
        c.emit_op(OP_GLOBAL_U, glob(n));
    }

    u32 slot_for(const std::string& n) { return scope && !scope->top ? local(n) : glob(n); }
    void store_slot(bool is_local, u32 slot, Code& c) {
        c.emit_op(is_local ? OP_SETLOCAL_U : OP_SETGLOBAL_U, slot);
    }
    void load_slot(bool is_local, u32 slot, Code& c) {
        c.emit_op(is_local ? OP_LOCAL_U : OP_GLOBAL_U, slot);
    }

    void compile_bin(const Expr& e, Code& c) {
        if (e.binop == B_AND || e.binop == B_OR) {
            compile_expr(*e.a, c);
            c.emit(e.binop == B_AND ? OP_JIFK : OP_JITK);
            size_t f = c.fixup32();
            c.emit(OP_POP);
            compile_expr(*e.b, c);
            c.patch(f, c.here());
            return;
        }
        compile_expr(*e.a, c);
        compile_expr(*e.b, c);
        switch (e.binop) {
            case B_ADD: c.emit(OP_ADD); break;
            case B_SUB: c.emit(OP_SUB); break;
            case B_MUL: c.emit(OP_MUL); break;
            case B_DIV: c.emit(OP_DIV); break;
            case B_MOD: c.emit(OP_MOD); break;
            case B_POW: c.emit(OP_POW); break;
            case B_EQ:  c.emit(OP_EQ); break;
            case B_NE:  c.emit(OP_NE); break;
            case B_LT:  c.emit(OP_LT); break;
            case B_LE:  c.emit(OP_LE); break;
            case B_GT:  c.emit(OP_GT); break;
            case B_GE:  c.emit(OP_GE); break;
            default: break;
        }
    }

    // ---- statements -------------------------------------------------------
    void compile_stmt(const Stmt& s, Code& c) {
        switch (s.k) {
            case Stmt::EXPR_: compile_expr(s.a, c); c.emit(OP_POP); break;
            case Stmt::SET_:  compile_set(s, c); break;
            case Stmt::OUT_: {
                for (auto& a : s.args) compile_expr(a, c);
                c.emit_op(OP_BUILTIN_U, builtin_id("print"));
                c.emit_u32((u32)s.args.size());
                c.emit(OP_POP);
                break;
            }
            case Stmt::PUSH_: {
                load_lvalue(s.name, c);
                compile_expr(s.a, c);
                c.emit_op(OP_BUILTIN_U, builtin_id("push"));
                c.emit_u32(2);
                c.emit(OP_POP);
                break;
            }
            case Stmt::RET_: compile_expr(s.a, c); c.emit(OP_RET); break;
            case Stmt::IF_:   compile_if(s, c); break;
            case Stmt::WHILE_: compile_while(s, c); break;
            case Stmt::LOOPF_: compile_loopf(s, c); break;
            case Stmt::LOOPX_: compile_loopx(s, c); break;
            case Stmt::SAFE_:  compile_safe(s, c); break;
            case Stmt::BREAK_: {
                c.emit(OP_JMP);
                size_t f = c.fixup32();
                scope->breaks.push_back(f);
                break;
            }
            case Stmt::CONT_: {
                c.emit(OP_JMP);
                size_t f = c.fixup32();
                scope->conts.push_back(f);
                break;
            }
            default: break;
        }
    }

    void compile_set(const Stmt& s, Code& c) {
        // fast path: x = x + <expr>  ->  OP_ADD_SG_U (global/local fused)
        if (s.idx.k == Expr::NIL && s.idx.sval.empty() &&
            s.a.k == Expr::BIN_ && s.a.binop == B_ADD &&
            s.a.a && s.a.a->k == Expr::VAR_ && s.a.a->sval == s.name) {
            bool is_local = scope && !scope->top;
            if (is_local) {
                c.emit_op(OP_LOCAL_U, slot_for(s.name));   // x
                compile_expr(*s.a.b, c);                   // y   -> x + y
                c.emit(OP_ADD);
                c.emit_op(OP_SETLOCAL_U, slot_for(s.name));
                return;
            }
            load_lvalue(s.name, c);      // [x]
            compile_expr(*s.a.b, c);     // [x, i]
            c.emit_op(OP_ADD_SG_U, slot_for(s.name));
            return;
        }
        compile_expr(s.a, c);   // [rhs]
        if (s.idx.k == Expr::NIL && s.idx.sval.empty()) {
            bool is_local = scope && !scope->top;
            store_slot(is_local, slot_for(s.name), c);
        } else if (s.idx.k == Expr::ATTR_) {
            load_lvalue(s.name, c);             // [rhs, obj]
            c.emit_op(OP_SETATTR_U, attr(s.idx.sval));
        } else {
            load_lvalue(s.name, c);             // [rhs, seq]
            compile_expr(s.idx, c);             // [rhs, seq, key]
            c.emit(OP_SETIDX);
        }
    }

    void compile_if(const Stmt& s, Code& c) {
        std::vector<size_t> jmps;
        for (auto& arm : s.arms) {
            compile_expr(arm.first, c);
            c.emit(OP_JIF);
            size_t f = c.fixup32();
            for (auto& st : arm.second) compile_stmt(st, c);
            c.emit(OP_JMP);
            size_t j = c.fixup32();
            c.patch(f, c.here());
            jmps.push_back(j);
        }
        for (auto& st : s.els) compile_stmt(st, c);
        size_t end = c.here();
        for (size_t j : jmps) c.patch(j, end);
    }

    void compile_while(const Stmt& s, Code& c) {
        size_t lcond = c.here();
        compile_expr(s.a, c);
        c.emit(OP_JIF);
        size_t f = c.fixup32();
        size_t nbrk = scope->breaks.size(), ncont = scope->conts.size();
        for (auto& st : s.body) compile_stmt(st, c);
        // continue -> recheck condition
        for (size_t k = ncont; k < scope->conts.size(); k++) c.patch(scope->conts[k], lcond);
        scope->conts.resize(ncont);
        c.emit(OP_JMP);
        size_t back = c.fixup32();
        c.patch(back, lcond);
        size_t lend = c.here();
        c.patch(f, lend);
        for (size_t k = nbrk; k < scope->breaks.size(); k++) c.patch(scope->breaks[k], lend);
        scope->breaks.resize(nbrk);
    }

    void compile_loopf(const Stmt& s, Code& c) {
        u32 var = slot_for(s.name);
        u32 endS = slot_for("\x01end:" + s.name);
        u32 stepS = slot_for("\x01step:" + s.name);
        bool is_local = scope && !scope->top;

        compile_expr(s.a, c); store_slot(is_local, var, c);
        compile_expr(s.b, c); store_slot(is_local, endS, c);
        if (s.step.k != Expr::NIL) compile_expr(s.step, c);
        else c.emit_op(OP_CONST_U, intc(1));
        store_slot(is_local, stepS, c);

        // direction: step >= 0 -> ascending
        load_slot(is_local, stepS, c);
        c.emit_op(OP_CONST_U, intc(0));
        c.emit(OP_GE);
        c.emit(OP_JIF);
        size_t is_neg = c.fixup32();

        // ascending precheck: if var > end -> skip loop
        load_slot(is_local, var, c); load_slot(is_local, endS, c);
        c.emit(OP_GT);
        c.emit(OP_JIT);
        size_t done_asc = c.fixup32();

        size_t lbody_asc = c.here();
        size_t nbrk = scope->breaks.size(), ncont = scope->conts.size();
        for (auto& st : s.body) compile_stmt(st, c);
        size_t next = c.here();
        for (size_t k = ncont; k < scope->conts.size(); k++) c.patch(scope->conts[k], next);
        scope->conts.resize(ncont);
        c.emit(is_local ? OP_RANGE_LE : OP_RANGE_LE_G);
        c.emit_u32(var); c.emit_u32(endS); c.emit_u32(stepS);
        size_t back_asc = c.fixup32();
        size_t fail_asc = c.fixup32();
        c.patch_rel(back_asc, lbody_asc, 8);

        c.patch(is_neg, c.here());
        // descending precheck: if var < end -> skip loop
        load_slot(is_local, var, c); load_slot(is_local, endS, c);
        c.emit(OP_LT);
        c.emit(OP_JIT);
        size_t done_desc = c.fixup32();

        size_t lbody_desc = c.here();
        size_t nbrk2 = scope->breaks.size(), ncont2 = scope->conts.size();
        for (auto& st : s.body) compile_stmt(st, c);
        size_t next2 = c.here();
        for (size_t k = ncont2; k < scope->conts.size(); k++) c.patch(scope->conts[k], next2);
        scope->conts.resize(ncont2);
        c.emit(is_local ? OP_RANGE_GE : OP_RANGE_GE_G);
        c.emit_u32(var); c.emit_u32(endS); c.emit_u32(stepS);
        size_t back_desc = c.fixup32();
        size_t fail_desc = c.fixup32();
        c.patch_rel(back_desc, lbody_desc, 8);

        size_t lend = c.here();                 // after this, patch prechecks/fails
        c.patch(fail_asc, lend);
        c.patch(fail_desc, lend);
        c.patch(done_asc, lend);
        c.patch(done_desc, lend);
        for (size_t k = nbrk; k < scope->breaks.size(); k++) c.patch(scope->breaks[k], lend);
        scope->breaks.resize(nbrk);
        for (size_t k = nbrk2; k < scope->breaks.size(); k++) c.patch(scope->breaks[k], lend);
        scope->breaks.resize(nbrk2);
    }

    void compile_loopx(const Stmt& s, Code& c) {
        u32 var = slot_for(s.name);
        bool is_local = scope && !scope->top;
        compile_expr(s.b, c);
        c.emit(OP_ITER_INIT);                    // [seq, 0]
        size_t lnext = c.here();
        c.emit(OP_ITER_NEXT);
        size_t f = c.fixup32();
        store_slot(is_local, var, c);            // consume item
        size_t nbrk = scope->breaks.size(), ncont = scope->conts.size();
        for (auto& st : s.body) compile_stmt(st, c);
        size_t next = c.here();                  // continue target: next iteration
        for (size_t k = ncont; k < scope->conts.size(); k++) c.patch(scope->conts[k], next);
        scope->conts.resize(ncont);
        c.emit(OP_JMP);                          // [seq, idx+1] (item consumed above)
        size_t back = c.fixup32();
        c.patch(back, lnext);
        size_t lend = c.here();
        c.patch(f, lend);
        c.emit(OP_ITER_END);                     // [seq, idx] -> pop both
        for (size_t k = nbrk; k < scope->breaks.size(); k++) c.patch(scope->breaks[k], lend);
        scope->breaks.resize(nbrk);
    }

    void compile_safe(const Stmt& s, Code& c) {
        c.emit(OP_SAFE_I);
        size_t f = c.fixup32();
        for (auto& st : s.body) compile_stmt(st, c);
        c.emit(OP_END_SAFE);
        c.emit(OP_JMP);
        size_t j = c.fixup32();
        c.patch(f, c.here());
        // catch target: error value already pushed by VM
        if (s.has_exc) {
            bool is_local = scope && !scope->top;
            store_slot(is_local, slot_for(s.exc), c);
        } else c.emit(OP_POP);
        for (auto& st : s.els) compile_stmt(st, c);
        c.patch(j, c.here());
    }
};

} // anonymous namespace

// ---------------------------------------------------------------------------
// public: compile AST -> module
// ---------------------------------------------------------------------------
Module compile_program(const Program& prog) {
    Module m;
    Compiler comp(m);

    m.funcs.push_back(Function{});
    m.func_names.push_back("main");
    for (const auto& f : prog.funcs) {
        m.funcs.push_back(Function{});
        m.func_names.push_back(f.name);
        comp.funcs[f.name] = (u32)(m.funcs.size() - 1);
    }

    // ---- main (top level) ----
    {
        Compiler::FuncScope sc;
        sc.fn = &m.funcs[0];
        sc.nlocals = 0;
        sc.top = true;
        comp.scope = &sc;
        Code c(&m, &m.funcs[0]);
        for (const auto& st : prog.stmts) {
            if (st.k == Stmt::FN_) continue;
            comp.compile_stmt(st, c);
        }
        c.emit(OP_NULL);
        c.emit(OP_RET);
        m.funcs[0].nparams = 0;
        m.funcs[0].nlocals = 0;
        comp.scope = nullptr;
    }

    // ---- user functions ----
    for (const auto& f : prog.funcs) {
        u32 idx = comp.funcs[f.name];
        Compiler::FuncScope sc;
        sc.fn = &m.funcs[idx];
        sc.nlocals = (u32)f.params.size();
        for (u32 i = 0; i < (u32)f.params.size(); i++) sc.locals[f.params[i]] = i;
        // Python-like scoping: pre-collect all assigned names as locals
        std::vector<std::string> assigns;
        Compiler::collect_assigns(f.body, assigns);
        for (auto& a : assigns)
            if (!sc.locals.count(a)) sc.locals[a] = sc.nlocals++;
        sc.top = false;
        comp.scope = &sc;

        Code c(&m, &m.funcs[idx]);
        for (const auto& st : f.body) comp.compile_stmt(st, c);
        c.emit(OP_NULL);
        c.emit(OP_RET);
        m.funcs[idx].nparams = (u32)f.params.size();
        m.funcs[idx].nlocals = sc.nlocals;
        comp.scope = nullptr;
    }

    return m;
}

// ---------------------------------------------------------------------------
// serialization (.xbc, little-endian)
// ---------------------------------------------------------------------------
static void put_u32(std::vector<u8>& v, u32 x) { for (int i = 0; i < 4; i++) v.push_back((u8)((x >> (8 * i)) & 0xFF)); }
static void put_str(std::vector<u8>& v, const std::string& s) {
    put_u32(v, (u32)s.size());
    v.insert(v.end(), s.begin(), s.end());
}
static u32 get_u32(const u8*& p) { u32 x = 0; for (int i = 0; i < 4; i++) x |= ((u32)p[i]) << (8 * i); p += 4; return x; }
static std::string get_str(const u8*& p) {
    u32 n = get_u32(p);
    std::string s((const char*)p, n);
    p += n;
    return s;
}

std::vector<u8> save_module(const Module& m) {
    std::vector<u8> v;
    v.insert(v.end(), {'X', 'B', 'C', '1'});
    put_u32(v, m.version);
    put_u32(v, (u32)m.strings.size());
    for (auto& s : m.strings) put_str(v, s);
    put_u32(v, (u32)m.globals.size());
    for (auto& s : m.globals) put_str(v, s);
    put_u32(v, (u32)m.attr_names.size());
    for (auto& s : m.attr_names) put_str(v, s);
    put_u32(v, (u32)m.funcs.size());
    for (auto& f : m.funcs) {
        put_u32(v, f.nparams);
        put_u32(v, f.nlocals);
        put_u32(v, (u32)f.code.size());
        v.insert(v.end(), f.code.begin(), f.code.end());
    }
    put_u32(v, (u32)m.func_names.size());
    for (auto& s : m.func_names) put_str(v, s);
    put_u32(v, (u32)m.constants.size());
    for (auto& cst : m.constants)
        for (int i = 0; i < 8; i++) v.push_back((u8)((cst.bits >> (8 * i)) & 0xFF));
    return v;
}

Module load_module(const u8* data, size_t len) {
    if (len < 8 || std::memcmp(data, "XBC1", 4) != 0) throw XppError("not a valid .xbc module");
    const u8* p = data + 4;
    Module m;
    m.version = get_u32(p);
    u32 ns = get_u32(p);
    m.strings.reserve(ns);
    for (u32 i = 0; i < ns; i++) m.strings.push_back(get_str(p));
    u32 ng = get_u32(p);
    m.globals.reserve(ng);
    for (u32 i = 0; i < ng; i++) m.globals.push_back(get_str(p));
    u32 na = get_u32(p);
    m.attr_names.reserve(na);
    for (u32 i = 0; i < na; i++) m.attr_names.push_back(get_str(p));
    u32 nf = get_u32(p);
    for (u32 i = 0; i < nf; i++) {
        Function f;
        f.nparams = get_u32(p);
        f.nlocals = get_u32(p);
        u32 nc = get_u32(p);
        if (nc > len) throw XppError("corrupt .xbc function");
        f.code.assign(p, p + nc);
        p += nc;
        m.funcs.push_back(std::move(f));
    }
    u32 nfn = get_u32(p);
    for (u32 i = 0; i < nfn; i++) m.func_names.push_back(get_str(p));
    u32 nc = get_u32(p);
    for (u32 i = 0; i < nc; i++) {
        u64 bits = 0;
        for (int j = 0; j < 8; j++) bits |= ((u64)p[j]) << (8 * j);
        p += 8;
        m.constants.push_back(Value{bits});
    }
    return m;
}

// ---------------------------------------------------------------------------
// disassembler
// ---------------------------------------------------------------------------
static const char* opname(u8 op) {
    switch (op) {
        case OP_HALT: return "HALT";
        case OP_NULL: return "NULL";
        case OP_TRUE: return "TRUE";
        case OP_FALSE: return "FALSE";
        case OP_CONST_U: return "CONST";
        case OP_FUNC_U: return "FUNC";
        case OP_BUILTINV_U: return "BUILTINV";
        case OP_LOCAL_U: return "LOCAL";
        case OP_GLOBAL_U: return "GLOBAL";
        case OP_SETLOCAL_U: return "SETLOCAL";
        case OP_SETGLOBAL_U: return "SETGLOBAL";
        case OP_POP: return "POP";
        case OP_DUP: return "DUP";
        case OP_SWAP: return "SWAP";
        case OP_ADD: return "ADD";
        case OP_SUB: return "SUB";
        case OP_MUL: return "MUL";
        case OP_DIV: return "DIV";
        case OP_MOD: return "MOD";
        case OP_POW: return "POW";
        case OP_NEG: return "NEG";
        case OP_EQ: return "EQ";
        case OP_NE: return "NE";
        case OP_LT: return "LT";
        case OP_LE: return "LE";
        case OP_GT: return "GT";
        case OP_GE: return "GE";
        case OP_AND: return "AND";
        case OP_OR: return "OR";
        case OP_NOT: return "NOT";
        case OP_JMP: return "JMP";
        case OP_JIF: return "JIF";
        case OP_JIT: return "JIT";
        case OP_JIFK: return "JIFK";
        case OP_JITK: return "JITK";
        case OP_CALL_U: return "CALL";
        case OP_RET: return "RET";
        case OP_MAKELIST_U: return "MAKELIST";
        case OP_MAKEDICT_U: return "MAKEDICT";
        case OP_IDX: return "IDX";
        case OP_SETIDX: return "SETIDX";
        case OP_ATTR_U: return "ATTR";
        case OP_SETATTR_U: return "SETATTR";
        case OP_BUILTIN_U: return "BUILTIN";
        case OP_ITER_INIT: return "ITER_INIT";
        case OP_ITER_NEXT: return "ITER_NEXT";
        case OP_ITER_END: return "ITER_END";
        case OP_SAFE_I: return "SAFE";
        case OP_END_SAFE: return "END_SAFE";
        case OP_RAISE: return "RAISE";
        case OP_TRACE: return "TRACE";
        case OP_RANGE_LE: return "RANGE_LE";
        case OP_RANGE_GE: return "RANGE_GE";
        case OP_ADD_SG_U: return "ADD_SG";
        case OP_RANGE_LE_G: return "RANGE_LE_G";
        case OP_RANGE_GE_G: return "RANGE_GE_G";
        default: return "?";
    }
}

std::string disassemble(const Module& m) {
    std::ostringstream os;
    for (size_t fi = 0; fi < m.funcs.size(); fi++) {
        const auto& f = m.funcs[fi];
        const std::string& name = fi < m.func_names.size() ? m.func_names[fi] : "?";
        os << "fn " << name << " (params=" << f.nparams << ", locals=" << f.nlocals << ")\n";
        const auto& code = f.code;
        size_t i = 0;
        while (i < code.size()) {
            u8 op = code[i];
            os << "  " << i << "  " << opname(op);
            size_t opi = i;
            i++;
            bool is_u32 = op == OP_CONST_U || op == OP_FUNC_U || op == OP_BUILTINV_U ||
                         op == OP_LOCAL_U || op == OP_GLOBAL_U || op == OP_SETLOCAL_U ||
                         op == OP_SETGLOBAL_U || op == OP_CALL_U || op == OP_MAKELIST_U ||
                         op == OP_MAKEDICT_U || op == OP_ATTR_U || op == OP_SETATTR_U ||
                         op == OP_BUILTIN_U || op == OP_TRACE || op == OP_ADD_SG_U;
            bool is_i32 = op == OP_JMP || op == OP_JIF || op == OP_JIT || op == OP_JIFK ||
                          op == OP_JITK || op == OP_ITER_NEXT || op == OP_SAFE_I;
            if (op == OP_RANGE_LE || op == OP_RANGE_GE || op == OP_RANGE_LE_G || op == OP_RANGE_GE_G) {
                u32 v0 = 0, v1 = 0, v2 = 0;
                i32 b0 = 0, f0 = 0;
                for (int k = 0; k < 4; k++) { v0 |= ((u32)code[i+k]) << (8*k); v1 |= ((u32)code[i+4+k]) << (8*k); v2 |= ((u32)code[i+8+k]) << (8*k); }
                for (int k = 0; k < 4; k++) { b0 |= ((u32)code[i+12+k]) << (8*k); f0 |= ((u32)code[i+16+k]) << (8*k); }
                i += 20;
                os << "  " << v0 << " " << v1 << " " << v2
                   << "  back-> " << (i + b0) << "  fail-> " << (i + f0);
            } else
            if (is_u32 || is_i32) {
                u32 v = 0;
                for (int k = 0; k < 4; k++) v |= ((u32)code[i + k]) << (8 * k);
                i += 4;
                if (is_u32) {
                    os << "  " << v;
                    if (op == OP_CONST_U && v < m.constants.size()) {
                        const Value& cv = m.constants[v];
                        if (cv.is_int()) os << "  ; int " << cv.as_int();
                        else if (cv.is_num()) os << "  ; float " << cv.as_double();
                        else if (cv.is_str() && cv.payload() < m.strings.size()) os << "  ; str \"" << m.strings[cv.payload()] << "\"";
                    }
                    if (op == OP_FUNC_U && v < m.func_names.size()) os << "  ; " << m.func_names[v];
                    if (op == OP_GLOBAL_U && v < m.globals.size()) os << "  ; " << m.globals[v];
                    if (op == OP_ATTR_U || op == OP_SETATTR_U) if (v < m.attr_names.size()) os << "  ; ." << m.attr_names[v];
                    if (op == OP_BUILTINV_U && v != 0xFFFFFFFFu) os << "  ; " << builtin_name(v);
                    if (op == OP_TRACE && v < m.func_names.size()) os << "  ; " << m.func_names[v];
                } else {
                    os << "  -> " << (i + (i32)v) << "  ; target";
                }
            }
            if (op == OP_BUILTIN_U) {
                // second operand: arg count; first operand was the builtin id
                u32 n = 0;
                for (int k = 0; k < 4; k++) n |= ((u32)code[i + k]) << (8 * k);
                i += 4;
                u32 bid = 0;
                for (int k = 0; k < 4; k++) bid |= ((u32)code[opi + 1 + k]) << (8 * k);
                os << "  args=" << n << "  ; " << builtin_name(bid);
            }
            os << "\n";
        }
        os << "end\n\n";
    }
    return os.str();
}

} // namespace xpp
