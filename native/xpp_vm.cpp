// ============================================================================
//  xpp_vm.cpp – ZITR: stack-based bytecode VM (NaN-boxed values)
//  X++ v0.4.1 – native VM core (zero dependencies)
// ============================================================================
#include "xpp.hpp"
#include <cmath>
#include <cstdio>
#include <algorithm>

namespace xpp {

namespace {
inline u32 rd32(const std::vector<u8>& c, size_t& ip) {
    u32 v = 0;
    for (int i = 0; i < 4; i++) v |= ((u32)c[ip + i]) << (8 * i);
    ip += 4;
    return v;
}
inline i32 rd32s(const std::vector<u8>& c, size_t& ip) {
    return (i32)rd32(c, ip);
}
} // namespace

// ---------------------------------------------------------------------------
VM::VM(const Module& m) : mod(m), globals(m.globals.size(), Value::nil()) {
    for (u32 i = 0; i < (u32)m.constants.size(); i++) {
        Value v = m.constants[i];
        if (v.is_str()) {
            u64 idx = v.payload();
            if (idx >= m.strings.size()) throw XppError("corrupt module: string constant");
            v = Value::str(arena.make_string(m.strings[idx]));
        }
        mod.constants[i] = v;
    }
}

// public entry: calls main()
Value VM::run(const std::vector<Value>& args) {
    Obj* o = arena.make_list();
    o->items = args;
    for (u32 i = 0; i < (u32)globals.size(); i++)
        if (mod.globals[i] == "ARGS") globals[i] = Value::list(o);
    return call_func(0, {});
}

Value VM::call_func(u32 fidx, const std::vector<Value>& args) {
    if (fidx >= mod.funcs.size()) throw XppError("call to unknown function");
    Frame f(fidx, &mod.funcs[fidx], stack_.size());
    for (u32 i = 0; i < (u32)args.size() && i < mod.funcs[fidx].nparams; i++)
        f.locals[i] = args[i];
    frames_.push_back(std::move(f));
    return run_loop();   // returns when the frame stack empties
}

void VM::raise(const Value& v) {
    throw XppError(to_str(v, arena));
}

[[noreturn]] void VM::type_error(const std::string& msg) const {
    throw XppError(msg);
}

// ---------------------------------------------------------------------------
// run_loop – FLAT (non-recursive) dispatch. X++ calls push a Frame and the
// loop re-fetches the new frame; returns only when the whole frame stack
// unwinds. This keeps deep X++ recursion (10k+) safe.
// ---------------------------------------------------------------------------
Value VM::run_loop() {
restart:
    try {
        while (true) {
            Frame& f = frames_.back();
            const std::vector<u8>& c = f.fn->code;
            u8 op = c[f.ip++];
            switch (op) {
                case OP_HALT:   return Value::nil();
                case OP_NULL:   stack_.push_back(Value::nil()); break;
                case OP_TRUE:   stack_.push_back(Value::boolean(true)); break;
                case OP_FALSE:  stack_.push_back(Value::boolean(false)); break;

                case OP_CONST_U: {
                    u32 i = rd32(c, f.ip);
                    if (i >= mod.constants.size()) type_error("constant index out of range");
                    stack_.push_back(mod.constants[i]);
                    break;
                }
                case OP_FUNC_U: { u32 i = rd32(c, f.ip); stack_.push_back(Value::func(i)); break; }
                case OP_BUILTINV_U: { u32 i = rd32(c, f.ip); stack_.push_back(Value::builtin(i)); break; }

                case OP_LOCAL_U: {
                    u32 i = rd32(c, f.ip);
                    if (i >= f.locals.size()) type_error("local index out of range");
                    stack_.push_back(f.locals[i]);
                    break;
                }
                case OP_GLOBAL_U: {
                    u32 i = rd32(c, f.ip);
                    if (i >= globals.size()) type_error("global index out of range");
                    stack_.push_back(globals[i]);
                    break;
                }
                case OP_SETLOCAL_U: {
                    u32 i = rd32(c, f.ip);
                    if (stack_.size() < f.stack_base + 1) type_error("stack underflow (compiler bug)");
                    f.locals[i] = stack_.back();
                    stack_.pop_back();
                    break;
                }
                case OP_SETGLOBAL_U: {
                    u32 i = rd32(c, f.ip);
                    if (stack_.size() < f.stack_base + 1) type_error("stack underflow (compiler bug)");
                    globals[i] = stack_.back();
                    stack_.pop_back();
                    break;
                }
                case OP_POP:
                    if (stack_.size() < f.stack_base + 1) type_error("stack underflow (compiler bug)");
                    stack_.pop_back();
                    break;
                case OP_DUP:
                    if (stack_.size() < f.stack_base + 1) type_error("stack underflow (compiler bug)");
                    stack_.push_back(stack_.back());
                    break;
                case OP_SWAP:
                    if (stack_.size() < f.stack_base + 2) type_error("stack underflow (compiler bug)");
                    std::swap(stack_[stack_.size() - 1], stack_[stack_.size() - 2]);
                    break;

                // -- arithmetic -------------------------------------------------
                case OP_ADD: case OP_SUB: case OP_MUL: case OP_DIV: case OP_MOD: case OP_POW: {
                    if (stack_.size() < f.stack_base + 2) type_error("stack underflow (compiler bug)");
                    Value b = stack_.back(); stack_.pop_back();
                    Value a = stack_.back(); stack_.pop_back();
                    Value r = op == OP_ADD ? value_add(a, b, arena)
                           : op == OP_SUB ? value_sub(a, b, arena)
                           : op == OP_MUL ? value_mul(a, b, arena)
                           : op == OP_DIV ? value_div(a, b, arena)
                           : op == OP_MOD ? value_mod(a, b, arena)
                                          : value_pow(a, b, arena);
                    stack_.push_back(r);
                    break;
                }
                case OP_NEG: {
                    if (stack_.size() < f.stack_base + 1) type_error("stack underflow (compiler bug)");
                    Value a = stack_.back(); stack_.pop_back();
                    if (a.is_int()) stack_.push_back(Value::integer(-a.as_int()));
                    else if (a.is_num()) stack_.push_back(Value::real(-a.as_double()));
                    else type_error("unary '-' needs a number");
                    break;
                }
                case OP_NOT: {
                    if (stack_.size() < f.stack_base + 1) type_error("stack underflow (compiler bug)");
                    Value a = stack_.back(); stack_.pop_back();
                    stack_.push_back(Value::boolean(!a.truthy()));
                    break;
                }

                // -- compare ----------------------------------------------------
                case OP_EQ: case OP_NE: {
                    if (stack_.size() < f.stack_base + 2) type_error("stack underflow (compiler bug)");
                    Value b = stack_.back(); stack_.pop_back();
                    Value a = stack_.back(); stack_.pop_back();
                    bool eq = value_equal(a, b, arena);
                    stack_.push_back(Value::boolean(op == OP_EQ ? eq : !eq));
                    break;
                }
                case OP_LT: case OP_LE: case OP_GT: case OP_GE: {
                    if (stack_.size() < f.stack_base + 2) type_error("stack underflow (compiler bug)");
                    Value b = stack_.back(); stack_.pop_back();
                    Value a = stack_.back(); stack_.pop_back();
                    int cmp;
                    if (a.is_number() && b.is_number()) {
                        double x = a.is_int() ? (double)a.as_int() : a.as_double();
                        double y = b.is_int() ? (double)b.as_int() : b.as_double();
                        cmp = x < y ? -1 : (x > y ? 1 : 0);
                    } else if (a.is_str() && b.is_str()) cmp = value_compare(a, b, arena);
                    else type_error("comparison requires two numbers or two strings");
                    bool r = false;
                    if (op == OP_LT) r = cmp < 0;
                    else if (op == OP_LE) r = cmp <= 0;
                    else if (op == OP_GT) r = cmp > 0;
                    else r = cmp >= 0;
                    stack_.push_back(Value::boolean(r));
                    break;
                }

                // -- jumps ------------------------------------------------------
                case OP_JMP:  f.ip += (size_t)(i64)rd32s(c, f.ip); break;
                case OP_JIF: {
                    if (stack_.size() < f.stack_base + 1) type_error("stack underflow (compiler bug)");
                    i32 off = rd32s(c, f.ip);
                    Value v = stack_.back(); stack_.pop_back();
                    if (!v.truthy()) f.ip += (size_t)(i64)off;
                    break;
                }
                case OP_JIT: {
                    if (stack_.size() < f.stack_base + 1) type_error("stack underflow (compiler bug)");
                    i32 off = rd32s(c, f.ip);
                    Value v = stack_.back(); stack_.pop_back();
                    if (v.truthy()) f.ip += (size_t)(i64)off;
                    break;
                }
                case OP_JIFK: {
                    if (stack_.size() < f.stack_base + 1) type_error("stack underflow (compiler bug)");
                    i32 off = rd32s(c, f.ip);
                    if (!stack_.back().truthy()) f.ip += (size_t)(i64)off;
                    break;
                }
                case OP_JITK: {
                    if (stack_.size() < f.stack_base + 1) type_error("stack underflow (compiler bug)");
                    i32 off = rd32s(c, f.ip);
                    if (stack_.back().truthy()) f.ip += (size_t)(i64)off;
                    break;
                }

                // -- calls (flat: push frame, continue loop) --------------------
                case OP_CALL_U: {
                    u32 n = rd32(c, f.ip);
                    if (stack_.size() < f.stack_base + n + 1) type_error("stack underflow (compiler bug)");
                    size_t base = stack_.size() - n;
                    Value callee = stack_[base - 1];
                    if (callee.is_builtin()) {
                        std::vector<Value> args(stack_.begin() + base, stack_.end());
                        stack_.resize(base - 1);
                        std::string err;
                        Value r = builtin_call(*this, callee.as_builtin(), args, &err);
                        if (!err.empty()) throw XppError(err);
                        stack_.push_back(r);
                    } else if (callee.is_func()) {
                        u32 fidx = callee.as_func();
                        if (fidx >= mod.funcs.size()) type_error("call to unknown function");
                        Frame nf(fidx, &mod.funcs[fidx], base - 1);
                        for (u32 i = 0; i < n && i < mod.funcs[fidx].nparams; i++)
                            nf.locals[i] = stack_[base + i];
                        stack_.resize(base - 1);
                        frames_.push_back(std::move(nf));
                        continue;   // re-fetch frame; no C++ recursion
                    } else {
                        type_error("attempt to call a non-function value");
                    }
                    break;
                }
                case OP_RET: {
                    if (stack_.size() < f.stack_base + 1) type_error("stack underflow (compiler bug)");
                    Value r = stack_.back();
                    stack_.pop_back();
                    stack_.resize(f.stack_base);
                    stack_.push_back(r);
                    frames_.pop_back();
                    if (frames_.empty()) return r;   // main returned
                    continue;                         // back in caller
                }

                // -- collections ------------------------------------------------
                case OP_MAKELIST_U: {
                    u32 n = rd32(c, f.ip);
                    if (stack_.size() < f.stack_base + n) type_error("stack underflow (compiler bug)");
                    Obj* o = arena.make_list();
                    o->items.resize(n);
                    for (u32 i = 0; i < n; i++) { o->items[n - 1 - i] = stack_.back(); stack_.pop_back(); }
                    stack_.push_back(Value::list(o));
                    break;
                }
                case OP_MAKEDICT_U: {
                    u32 np = rd32(c, f.ip);
                    if (stack_.size() < f.stack_base + np * 2) type_error("stack underflow (compiler bug)");
                    Obj* o = arena.make_dict();
                    o->pairs.resize(np);
                    for (u32 i = 0; i < np; i++) {
                        Value v = stack_.back(); stack_.pop_back();
                        Value k = stack_.back(); stack_.pop_back();
                        o->pairs[np - 1 - i] = {to_str(k, arena), v};
                    }
                    stack_.push_back(Value::dict(o));
                    break;
                }
                case OP_IDX: {
                    if (stack_.size() < f.stack_base + 2) type_error("stack underflow (compiler bug)");
                    Value k = stack_.back(); stack_.pop_back();
                    Value seq = stack_.back(); stack_.pop_back();
                    if (seq.is_list()) {
                        if (!k.is_number()) type_error("list index must be a number");
                        i64 i = k.is_int() ? k.as_int() : (i64)k.as_double();
                        auto& items = seq.as_obj()->items;
                        if (i < 0) i += (i64)items.size();
                        if (i < 0 || (size_t)i >= items.size()) type_error("list index out of range");
                        stack_.push_back(items[(size_t)i]);
                    } else if (seq.is_str()) {
                        if (!k.is_number()) type_error("string index must be a number");
                        i64 i = k.is_int() ? k.as_int() : (i64)k.as_double();
                        const std::string& s = seq.as_obj()->s;
                        if (i < 0) i += (i64)s.size();
                        if (i < 0 || (size_t)i >= s.size()) type_error("string index out of range");
                        stack_.push_back(Value::str(arena.make_string(std::string(1, s[(size_t)i]))));
                    } else if (seq.is_dict()) {
                        std::string ks = k.is_str() ? k.as_obj()->s : to_str(k, arena);
                        bool found = false;
                        for (auto& p : seq.as_obj()->pairs)
                            if (p.first == ks) { stack_.push_back(p.second); found = true; break; }
                        if (!found) type_error("dict key not found: '" + ks + "'");
                    } else type_error("indexing requires list/string/dict");
                    break;
                }
                case OP_SETIDX: {
                    if (stack_.size() < f.stack_base + 3) type_error("stack underflow (compiler bug)");
                    Value k = stack_.back(); stack_.pop_back();
                    Value seq = stack_.back(); stack_.pop_back();
                    Value val = stack_.back(); stack_.pop_back();
                    if (seq.is_list()) {
                        if (!k.is_number()) type_error("list index must be a number");
                        i64 i = k.is_int() ? k.as_int() : (i64)k.as_double();
                        auto& items = seq.as_obj()->items;
                        if (i < 0) i += (i64)items.size();
                        if (i < 0 || (size_t)i >= items.size()) type_error("list index out of range");
                        items[(size_t)i] = val;
                    } else if (seq.is_dict()) {
                        std::string ks = k.is_str() ? k.as_obj()->s : to_str(k, arena);
                        bool found = false;
                        for (auto& p : seq.as_obj()->pairs)
                            if (p.first == ks) { p.second = val; found = true; break; }
                        if (!found) seq.as_obj()->pairs.push_back({ks, val});
                    } else type_error("index assignment requires list/dict");
                    break;
                }
                case OP_ATTR_U: {
                    u32 ai = rd32(c, f.ip);
                    if (stack_.size() < f.stack_base + 1) type_error("stack underflow (compiler bug)");
                    Value obj = stack_.back(); stack_.pop_back();
                    const std::string& name = mod.attr_names[ai];
                    if (obj.is_dict()) {
                        bool found = false;
                        for (auto& p : obj.as_obj()->pairs)
                            if (p.first == name) { stack_.push_back(p.second); found = true; break; }
                        if (!found) type_error("dict has no key '" + name + "'");
                    } else type_error("attribute access requires dict");
                    break;
                }
                case OP_SETATTR_U: {
                    u32 ai = rd32(c, f.ip);
                    if (stack_.size() < f.stack_base + 2) type_error("stack underflow (compiler bug)");
                    Value obj = stack_.back(); stack_.pop_back();
                    Value val = stack_.back(); stack_.pop_back();
                    const std::string& name = mod.attr_names[ai];
                    if (obj.is_dict()) {
                        bool found = false;
                        for (auto& p : obj.as_obj()->pairs)
                            if (p.first == name) { p.second = val; found = true; break; }
                        if (!found) obj.as_obj()->pairs.push_back({name, val});
                    } else type_error("attribute assignment requires dict");
                    break;
                }
                case OP_BUILTIN_U: {
                    u32 id = rd32(c, f.ip);
                    u32 n = rd32(c, f.ip);
                    if (stack_.size() < f.stack_base + n) type_error("stack underflow (compiler bug)");
                    size_t base = stack_.size() - n;
                    std::vector<Value> args(stack_.begin() + base, stack_.end());
                    stack_.resize(base);
                    std::string err;
                    Value r = builtin_call(*this, id, args, &err);
                    if (!err.empty()) throw XppError(err);
                    stack_.push_back(r);
                    break;
                }

                // -- iteration --------------------------------------------------
                case OP_ITER_INIT: {
                    if (stack_.size() < f.stack_base + 1) type_error("stack underflow (compiler bug)");
                    Value seq = stack_.back();
                    if (!(seq.is_list() || seq.is_str())) type_error("loop requires list or string");
                    stack_.push_back(Value::integer(0));   // [seq, 0]
                    break;
                }
                case OP_ITER_NEXT: {
                    if (stack_.size() < f.stack_base + 2) type_error("stack underflow (compiler bug)");
                    i32 off = rd32s(c, f.ip);
                    i64 idx = stack_[stack_.size() - 1].as_int();
                    Value seq = stack_[stack_.size() - 2];
                    size_t len = seq.is_list() ? seq.as_obj()->items.size() : seq.as_obj()->s.size();
                    if (idx >= (i64)len) {
                        f.ip += (size_t)(i64)off;
                    } else {
                        if (seq.is_list()) stack_.push_back(seq.as_obj()->items[(size_t)idx]);
                        else stack_.push_back(Value::str(arena.make_string(std::string(1, seq.as_obj()->s[(size_t)idx]))));
                        stack_[stack_.size() - 2] = Value::integer(idx + 1);
                    }
                    break;
                }
                case OP_ITER_END: {
                    if (stack_.size() < f.stack_base + 2) type_error("stack underflow (compiler bug)");
                    stack_.pop_back();
                    stack_.pop_back();
                    break;
                }

                // -- safe blocks ------------------------------------------------
                case OP_SAFE_I: {
                    i32 target = rd32s(c, f.ip);
                    f.catches.push_back({stack_.size(), f.ip + (size_t)(i64)target});
                    break;
                }
                case OP_END_SAFE:
                    if (f.catches.empty()) type_error("END_SAFE without SAFE");
                    f.catches.pop_back();
                    break;
                case OP_RAISE: {
                    if (stack_.size() < f.stack_base + 1) type_error("stack underflow (compiler bug)");
                    Value v = stack_.back(); stack_.pop_back();
                    raise(v);
                    break;
                }
                case OP_TRACE: rd32(c, f.ip); break;

                // -- fused range loops (hot path) ------------------------------
                case OP_RANGE_LE: case OP_RANGE_GE:
                case OP_RANGE_LE_G: case OP_RANGE_GE_G: {
                    u32 var = rd32(c, f.ip);
                    u32 end = rd32(c, f.ip);
                    u32 step = rd32(c, f.ip);
                    i32 back = rd32s(c, f.ip);
                    i32 fail = rd32s(c, f.ip);
                    bool is_g = op == OP_RANGE_LE_G || op == OP_RANGE_GE_G;
                    Value& v = is_g ? globals[var] : f.locals[var];
                    Value& e = is_g ? globals[end] : f.locals[end];
                    Value& s = is_g ? globals[step] : f.locals[step];
                    if (!(v.is_number() && e.is_number() && s.is_number()))
                        type_error("loop bounds must be numbers");
                    Value nv = value_add(v, s, arena);
                    double nx = nv.is_int() ? (double)nv.as_int() : nv.as_double();
                    double y = e.is_int() ? (double)e.as_int() : e.as_double();
                    bool asc = op == OP_RANGE_LE || op == OP_RANGE_LE_G;
                    bool in_range = asc ? (nx <= y) : (nx >= y);
                    if (in_range) {
                        v = nv;
                        f.ip += (size_t)(i64)back;
                    } else {
                        f.ip += (size_t)(i64)fail;
                    }
                    break;
                }
                case OP_ADD_SG_U: {
                    u32 gi = rd32(c, f.ip);
                    if (stack_.size() < f.stack_base + 2) type_error("stack underflow (compiler bug)");
                    Value b = stack_.back(); stack_.pop_back();
                    Value a = stack_.back(); stack_.pop_back();
                    if (gi >= globals.size()) type_error("global index out of range");
                    globals[gi] = value_add(a, b, arena);
                    break;
                }

                default:
                    type_error("unknown opcode " + std::to_string(op));
            }
        }
    } catch (const XppError& e) {
        // unwind one frame at a time; handle a safe/catch at the top frame
        while (!frames_.empty()) {
            Frame& f = frames_.back();
            if (!f.catches.empty()) {
                auto rec = f.catches.back();
                f.catches.pop_back();
                stack_.resize(rec.stack_depth);
                stack_.push_back(Value::str(arena.make_string(e.what())));
                f.ip = rec.ip_target;
                goto restart;
            }
            frames_.pop_back();
        }
        throw;
    }
}

} // namespace xpp
