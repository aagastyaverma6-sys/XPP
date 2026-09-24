// ============================================================================
//  X++ v0.4.1 – Native VM Core (ZCOM / ZITR / ZJIT)
//  Zero-dependency C++17. Runs on any OS with a C++ compiler; Python is NOT
//  required to run .xp programs once xppvm is built.
//
//  Value model: NaN-boxed 64-bit values.
//    * plain doubles are stored as their IEEE-754 bits
//    * everything else uses a quiet-NaN payload: 0xFFF0|tag in bits 48..63
//      and a 48-bit payload.
//  This keeps ZITR (interpreter) and ZJIT (native codegen) on one format.
//
//  Author: Aagastya Verma / Atom Software
//  License: GPL-3.0-or-later
// ============================================================================
#pragma once

#include <cstdint>
#include <cstddef>
#include <cstring>
#include <string>
#include <vector>
#include <memory>
#include <stdexcept>
#include <utility>

namespace xpp {

using u8  = std::uint8_t;
using u16 = std::uint16_t;
using u32 = std::uint32_t;
using u64 = std::uint64_t;
using i64 = std::int64_t;
using i32 = std::int32_t;

// ---------------------------------------------------------------------------
// Value
// ---------------------------------------------------------------------------
enum Tag : u64 {
    TAG_NIL   = 0,
    TAG_FALSE = 1,
    TAG_TRUE  = 2,
    TAG_INT   = 3,
    TAG_STR   = 4,
    TAG_LIST  = 5,
    TAG_DICT  = 6,
    TAG_FUNC  = 7,
    TAG_BUILT = 8,
};

inline u64   tag_bits(u64 tag, u64 payload) { return (0xFFF0ull << 48) | (tag << 48) | (payload & 0xFFFFFFFFFFFFull); }
inline u64   as_tag(u64 t, u64 payload)      { return tag_bits(t, payload); }

struct Obj;
struct Value {
    u64 bits;

    Value() : bits(tag_bits(TAG_NIL, 0)) {}
    explicit Value(u64 raw)   : bits(raw) {}
    explicit Value(double d) : bits(0) { std::memcpy(&bits, &d, 8); }
    explicit Value(i64 i)     : bits(tag_bits(TAG_INT, (u64)i)) {}

    static Value nil()    { return Value(tag_bits(TAG_NIL, 0)); }
    static Value boolean(bool b) { return Value(tag_bits(b ? TAG_TRUE : TAG_FALSE, 0)); }
    static Value integer(i64 i)  { return Value(i); }
    static Value real(double d)   { return Value(d); }
    static Value str(Obj* o)      { return Value(tag_bits(TAG_STR, reinterpret_cast<u64>(o))); }
    static Value list(Obj* o)     { return Value(tag_bits(TAG_LIST, reinterpret_cast<u64>(o))); }
    static Value dict(Obj* o)     { return Value(tag_bits(TAG_DICT, reinterpret_cast<u64>(o))); }
    static Value func(u32 idx)    { return Value(tag_bits(TAG_FUNC, idx)); }
    static Value builtin(u32 k)   { return Value(tag_bits(TAG_BUILT, k)); }

    u64 tag_of() const { return bits >> 48; }          // 0xFFF0|tag for tagged, else < 0xFFF0
    bool is_tagged() const { return (bits >> 48) >= 0xFFF0; }
    bool is_nil()    const { return (bits >> 48) == (0xFFF0 | TAG_NIL); }
    bool is_bool()   const { u64 t = bits >> 48; return t == (0xFFF0 | TAG_FALSE) || t == (0xFFF0 | TAG_TRUE); }
    bool is_true()   const { return (bits >> 48) == (0xFFF0 | TAG_TRUE); }
    bool is_false()  const { return (bits >> 48) == (0xFFF0 | TAG_FALSE); }
    bool is_int()    const { return (bits >> 48) == (0xFFF0 | TAG_INT); }
    bool is_num()    const { return (bits >> 48) < 0xFFF0; }   // plain double
    bool is_number() const { return is_num() || is_int(); }
    bool is_str()    const { return (bits >> 48) == (0xFFF0 | TAG_STR); }
    bool is_list()   const { return (bits >> 48) == (0xFFF0 | TAG_LIST); }
    bool is_dict()   const { return (bits >> 48) == (0xFFF0 | TAG_DICT); }
    bool is_func()   const { return (bits >> 48) == (0xFFF0 | TAG_FUNC); }
    bool is_builtin()const { return (bits >> 48) == (0xFFF0 | TAG_BUILT); }

    double    as_double() const { double d; std::memcpy(&d, &bits, 8); return d; }
    i64       as_int()    const { return static_cast<i64>((i64)(bits << 16) >> 16); }
    u64       payload()   const { return bits & 0xFFFFFFFFFFFFull; }
    Obj*      as_obj()    const { return reinterpret_cast<Obj*>(payload()); }
    u32       as_func()   const { return (u32)payload(); }
    u32       as_builtin()const { return (u32)payload(); }
    bool      truthy()    const;

    bool operator==(const Value& o) const { return bits == o.bits; }
};

// ---------------------------------------------------------------------------
// Objects (arena-allocated; freed when the VM dies -> no cycles to collect)
// ---------------------------------------------------------------------------
enum ObjKind { OBJ_STRING, OBJ_LIST, OBJ_DICT };

struct Obj {
    ObjKind kind;
    std::string s;                       // OBJ_STRING
    std::vector<Value> items;            // OBJ_LIST
    std::vector<std::pair<std::string, Value>> pairs;  // OBJ_DICT (ordered)
    Obj(ObjKind k) : kind(k) {}
};

struct Arena {
    std::vector<std::unique_ptr<Obj>> objs;
    Obj* make(ObjKind k) {
        objs.push_back(std::make_unique<Obj>(k));
        return objs.back().get();
    }
    Obj* make_string(const std::string& s) { Obj* o = make(OBJ_STRING); o->s = s; return o; }
    Obj* make_string(std::string&& s)      { Obj* o = make(OBJ_STRING); o->s = std::move(s); return o; }
    Obj* make_list()                       { return make(OBJ_LIST); }
    Obj* make_dict()                       { return make(OBJ_DICT); }
};

// ---------------------------------------------------------------------------
// Bytecode
// ---------------------------------------------------------------------------
enum Op : u8 {
    OP_HALT = 0,
    OP_NULL, OP_TRUE, OP_FALSE,
    OP_CONST_U,      // u32 const idx
    OP_FUNC_U,       // u32 function idx
    OP_BUILTINV_U,   // u32 builtin id
    OP_LOCAL_U,      // u32 idx        push local
    OP_GLOBAL_U,     // u32 idx        push global
    OP_SETLOCAL_U,   // u32 idx        pop -> local
    OP_SETGLOBAL_U,  // u32 idx        pop -> global
    OP_POP,
    OP_DUP,
    OP_SWAP,
    OP_ADD, OP_SUB, OP_MUL, OP_DIV, OP_MOD, OP_POW, OP_NEG,
    OP_EQ, OP_NE, OP_LT, OP_LE, OP_GT, OP_GE,
    OP_AND, OP_OR, OP_NOT,
    OP_JMP,          // i32
    OP_JIF,          // i32  (pop)
    OP_JIT,          // i32  (pop)
    OP_JIFK,         // i32  (keep)
    OP_JITK,         // i32  (keep)
    OP_CALL_U,       // u32 nargs
    OP_RET,          // value on top
    OP_MAKELIST_U,   // u32 n
    OP_MAKEDICT_U,   // u32 npairs
    OP_IDX,          // pop key, pop seq -> push
    OP_SETIDX,       // pop val, pop key, pop seq
    OP_ATTR_U,       // u32 name idx   pop obj -> push
    OP_SETATTR_U,    // u32 name idx   pop val, pop obj
    OP_BUILTIN_U,    // u32 id         pops args (known count) pushes result
    OP_ITER_INIT,    // pop seq; push seq; push int 0
    OP_ITER_NEXT,    // i32 fail: [seq, idx] -> done ? (pop2, jump) : (push item, idx+1)
    OP_ITER_END,     // pop seq, pop idx
    OP_SAFE_I,      // i32 catch target
    OP_END_SAFE,    // pop catch record
    OP_RAISE,       // value on top
    OP_TRACE,       // u32 func name idx (kept for future use)
    OP_RANGE_LE,    // u32 var, u32 end, u32 step, i32 back, i32 fail (locals)
    OP_RANGE_GE,    // u32 var, u32 end, u32 step, i32 back, i32 fail (locals)
    OP_ADD_SG_U,    // u32 global slot: pop a, pop b -> store a+b
    OP_RANGE_LE_G,  // same as RANGE_LE but slots are globals
    OP_RANGE_GE_G,  // same as RANGE_GE but slots are globals
};

// Serialized module (little-endian, version 1)
struct Function {
    u32 nparams = 0;
    u32 nlocals = 0;               // locals incl. params + hidden
    std::vector<u8> code;
};

struct Module {
    u32 version = 1;
    std::vector<Value> constants;      // STR payload = index into strings
    std::vector<std::string> strings;  // string pool for STR constants
    std::vector<std::string> globals;  // global name table
    std::vector<std::string> attr_names; // attribute/name table
    std::vector<Function> funcs;
    std::vector<std::string> func_names;
};

// ---------------------------------------------------------------------------
// Error
// ---------------------------------------------------------------------------
struct XppError : std::runtime_error {
    std::string trace;
    explicit XppError(const std::string& msg) : std::runtime_error(msg) {}
};

// ---------------------------------------------------------------------------
// AST (parser output, consumed by the bytecode compiler)
// ---------------------------------------------------------------------------
struct Expr;
struct Stmt;

struct Expr {
    enum K {
        NIL, TRUE_, FALSE_, INT_, FLOAT_, STR_,
        VAR_, LIST_, DICT_, CALL_, IDX_, ATTR_, BIN_,
        NEG_, NOT_, INPUT_, READ_, LEN_
    } k = NIL;
    i64 ival = 0;
    double fval = 0.0;
    std::string sval;         // STR_ text, VAR_ name, ATTR_ name, INPUT_ prompt
    u32 binop = 0;            // BIN_ op id (see BinOp)
    std::shared_ptr<Expr> a, b, c;   // children (max 3)
    std::vector<Expr> items;         // LIST_/DICT_/CALL_ args
};

enum BinOp : u32 {
    B_ADD = 0, B_SUB, B_MUL, B_DIV, B_MOD, B_POW,
    B_EQ, B_NE, B_LT, B_LE, B_GT, B_GE,
    B_AND, B_OR
};

struct Stmt {
    enum K {
        FN_, IF_, WHILE_, LOOPF_, LOOPX_, SAFE_,
        RET_, BREAK_, CONT_, OUT_, PUSH_, SET_, EXPR_
    } k;
    std::string name;               // FN_ name, PUSH_ list name, SET_ lvalue name
    std::vector<std::string> params;
    std::vector<Stmt> body;         // FN_/WHILE_/LOOPF_/LOOPX_ body, IF_ first arm body
    std::vector<std::pair<Expr, std::vector<Stmt>>> arms; // IF_/ELIF
    std::vector<Stmt> els;          // IF_ else body, SAFE_ fail body
    Expr a, b, c;                   // cond / from,to / iterable / rhs
    Expr step;                      // LOOPF_
    Expr idx;                       // SET_ index expr (optional)
    std::vector<Expr> args;         // OUT_
    std::string exc;                // SAFE_ exception var (empty = none)
    bool has_exc = false;
};

struct Program {
    // top-level statements
    std::vector<Stmt> stmts;
    // functions defined anywhere (name -> body)
    struct FnDef {
        std::string name;
        std::vector<std::string> params;
        std::vector<Stmt> body;
        u32 index = 0;
    };
    std::vector<FnDef> funcs;
};

// parse .xp source (strict pseudocode). Throws XppError with line info.
Program parse_program(const std::string& src);

// compile AST -> bytecode module
Module compile_program(const Program& prog);

// serialize / deserialize .xbc
std::vector<u8> save_module(const Module& m);
Module load_module(const u8* data, size_t len);   // throws XppError

// disassembler (for `xppvm disasm`)
std::string disassemble(const Module& m);

// ---------------------------------------------------------------------------
// VM (ZITR) / native (ZJIT)
// ---------------------------------------------------------------------------
struct CatchRec {
    size_t stack_depth = 0;
    size_t ip_target = 0;
};

struct Frame {
    u32 fidx = 0;
    const Function* fn = nullptr;
    size_t ip = 0;
    std::vector<Value> locals;
    std::vector<CatchRec> catches;
    size_t stack_base = 0;
    Frame() = default;
    Frame(u32 f, const Function* p, size_t base) : fidx(f), fn(p), stack_base(base) {
        locals.assign(p->nlocals, Value::nil());
    }
};

class VM {
public:
    explicit VM(const Module& m);
    // runs main() with given args (script args after file). Returns exit-ish value.
    Value run(const std::vector<Value>& args = {});
    // internal: one call into function idx with args (used by JIT glue)
    Value call_func(u32 fidx, const std::vector<Value>& args);

    Arena arena;
    Module mod;
    std::vector<Value> globals;
    std::vector<std::string> func_names;

private:
    std::vector<Value> stack_;
    std::vector<Frame> frames_;

    Value run_loop();
    void raise(const Value& v);
    [[noreturn]] void type_error(const std::string& msg) const;
};

// ZJIT – native AOT backend (generates portable C++ for the X++ program and
// compiles it with the system C++ compiler into a native binary).
bool zjit_available();
bool zjit_build(const std::string& src_path, const std::string& out_exe,
                const std::string& runtime_dir, bool verbose, std::string* err);
int  zjit_run(const std::string& src_path, const std::string& runtime_dir,
              bool verbose);

// ---------------------------------------------------------------------------
// CLI helpers
// ---------------------------------------------------------------------------
int cli_main(int argc, char** argv);

// builtins ------------------------------------------------------------------
u32 builtin_id(const std::string& name);   // 0xFFFFFFFF if unknown
std::string builtin_name(u32 id);
Value builtin_call(VM& vm, u32 id, const std::vector<Value>& args, std::string* err);

// value helpers --------------------------------------------------------------
std::string to_display_string(const Value& v, Arena& a);
std::string to_str(const Value& v, Arena& a);
bool value_equal(const Value& x, const Value& y, Arena& a);
int  value_compare(const Value& x, const Value& y, Arena& a); // -1/0/1, throws
Value value_add(const Value& x, const Value& y, Arena& a);
Value value_sub(const Value& x, const Value& y, Arena& a);
Value value_mul(const Value& x, const Value& y, Arena& a);
Value value_div(const Value& x, const Value& y, Arena& a);
Value value_mod(const Value& x, const Value& y, Arena& a);
Value value_pow(const Value& x, const Value& y, Arena& a);

} // namespace xpp
