// ============================================================================
//  xpp_values.cpp – NaN-boxed value helpers + builtins
//  X++ v0.4.1 – native VM core
// ============================================================================
#include "xpp.hpp"
#include <cmath>
#include <cstdio>
#include <iostream>
#include <fstream>
#include <algorithm>
#include <sstream>
#include <iomanip>

namespace xpp {

bool Value::truthy() const {
    if (is_nil()) return false;
    if (is_bool()) return is_true();
    if (is_int()) return as_int() != 0;
    if (is_num()) return as_double() != 0.0;
    // str/list/dict follow Python semantics: empty containers are falsy
    const Obj* o = as_obj();
    if (is_str()) return !o->s.empty();
    if (is_list()) return !o->items.empty();
    return !o->pairs.empty();
}

// ---------------------------------------------------------------------------
// Conversions
// ---------------------------------------------------------------------------
static std::string format_double(double d) {
    if (std::isnan(d)) return "nan";
    if (std::isinf(d)) return d > 0 ? "inf" : "-inf";
    if (d == (double)(i64)d && std::fabs(d) < 9.007199254740992e15) {
        char buf[32];
        std::snprintf(buf, sizeof(buf), "%lld", (long long)d);
        return buf;
    }
    std::ostringstream os;
    os << std::setprecision(15) << d;
    return os.str();
}

std::string to_str(const Value& v, Arena& a) {
    switch ((u32)v.tag_of()) {
        case (0xFFF0 | TAG_NIL):   return "nil";
        case (0xFFF0 | TAG_FALSE): return "false";
        case (0xFFF0 | TAG_TRUE):  return "true";
        case (0xFFF0 | TAG_INT): {
            char buf[32];
            std::snprintf(buf, sizeof(buf), "%lld", (long long)v.as_int());
            return buf;
        }
        case (0xFFF0 | TAG_STR):   return v.as_obj()->s;
        default:
            if (!v.is_tagged()) return format_double(v.as_double());
            return to_display_string(v, a);
    }
}

std::string to_display_string(const Value& v, Arena& a) {
    switch ((u32)v.tag_of()) {
        case (0xFFF0 | TAG_NIL):   return "nil";
        case (0xFFF0 | TAG_FALSE): return "false";
        case (0xFFF0 | TAG_TRUE):  return "true";
        case (0xFFF0 | TAG_INT): {
            char buf[32];
            std::snprintf(buf, sizeof(buf), "%lld", (long long)v.as_int());
            return buf;
        }
        case (0xFFF0 | TAG_STR):   return v.as_obj()->s;
        case (0xFFF0 | TAG_LIST): {
            Obj* o = v.as_obj();
            std::string r = "[";
            for (size_t i = 0; i < o->items.size(); i++) {
                if (i) r += ", ";
                r += to_display_string(o->items[i], a);
            }
            r += "]";
            return r;
        }
        case (0xFFF0 | TAG_DICT): {
            Obj* o = v.as_obj();
            std::string r = "{";
            for (size_t i = 0; i < o->pairs.size(); i++) {
                if (i) r += ", ";
                r += "\"" + o->pairs[i].first + "\": " + to_display_string(o->pairs[i].second, a);
            }
            r += "}";
            return r;
        }
        case (0xFFF0 | TAG_FUNC):   return "<fn>";
        case (0xFFF0 | TAG_BUILT):return "<builtin " + builtin_name(v.as_builtin()) + ">";
        default:
            if (!v.is_tagged()) return format_double(v.as_double());
            return "<?>";
    }
}

// ---------------------------------------------------------------------------
// Equality / comparison
// ---------------------------------------------------------------------------
bool value_equal(const Value& x, const Value& y, Arena&) {
    Arena dummy;
    if (x.is_number() && y.is_number()) {
        double a = x.is_int() ? (double)x.as_int() : x.as_double();
        double b = y.is_int() ? (double)y.as_int() : y.as_double();
        return a == b;
    }
    if (x.tag_of() != y.tag_of()) return false;
    switch ((u32)x.tag_of()) {
        case (0xFFF0 | TAG_STR): return x.as_obj()->s == y.as_obj()->s;
        case (0xFFF0 | TAG_LIST): {
            const auto& a = x.as_obj()->items;
            const auto& b = y.as_obj()->items;
            if (a.size() != b.size()) return false;
            for (size_t i = 0; i < a.size(); i++)
                if (!value_equal(a[i], b[i], dummy)) return false;
            return true;
        }
        case (0xFFF0 | TAG_DICT): {
            const auto& a = x.as_obj()->pairs;
            const auto& b = y.as_obj()->pairs;
            if (a.size() != b.size()) return false;
            for (auto& p : a) {
                bool found = false;
                for (auto& q : b)
                    if (p.first == q.first) { if (!value_equal(p.second, q.second, dummy)) return false; found = true; break; }
                if (!found) return false;
            }
            return true;
        }
        default: return x.bits == y.bits;
    }
}

int value_compare(const Value& x, const Value& y, Arena& a) {
    (void)a;
    if (x.is_number() && y.is_number()) {
        double dx = x.is_int() ? (double)x.as_int() : x.as_double();
        double dy = y.is_int() ? (double)y.as_int() : y.as_double();
        if (dx < dy) return -1;
        if (dx > dy) return 1;
        return 0;
    }
    if (x.is_str() && y.is_str()) {
        const std::string& sx = x.as_obj()->s;
        const std::string& sy = y.as_obj()->s;
        if (sx < sy) return -1;
        if (sx > sy) return 1;
        return 0;
    }
    throw XppError("comparison '<' '>' requires numbers or strings");
}

// ---------------------------------------------------------------------------
// Arithmetic
// ---------------------------------------------------------------------------
static bool both_strings(const Value& x, const Value& y) { return x.is_str() && y.is_str(); }

Value value_add(const Value& x, const Value& y, Arena& a) {
    if (both_strings(x, y)) return Value::str(a.make_string(x.as_obj()->s + y.as_obj()->s));
    if (x.is_str() || y.is_str()) {
        if (x.is_str() && y.is_number()) {
            std::string s = x.as_obj()->s + to_str(y, a);
            return Value::str(a.make_string(std::move(s)));
        }
        if (y.is_str() && x.is_number()) {
            std::string s = to_str(x, a) + y.as_obj()->s;
            return Value::str(a.make_string(std::move(s)));
        }
        throw XppError("cannot add string and non-string/non-number");
    }
    if (x.is_list() && y.is_list()) {
        Obj* o = a.make_list();
        o->items = x.as_obj()->items;
        o->items.insert(o->items.end(), y.as_obj()->items.begin(), y.as_obj()->items.end());
        return Value::list(o);
    }
    if (x.is_int() && y.is_int()) return Value::integer(x.as_int() + y.as_int());
    double r = (x.is_int() ? (double)x.as_int() : x.as_double()) +
               (y.is_int() ? (double)y.as_int() : y.as_double());
    return Value::real(r);
}

Value value_sub(const Value& x, const Value& y, Arena& a) {
    if (x.is_int() && y.is_int()) return Value::integer(x.as_int() - y.as_int());
    double r = (x.is_int() ? (double)x.as_int() : x.as_double()) -
               (y.is_int() ? (double)y.as_int() : y.as_double());
    return Value::real(r);
}

Value value_mul(const Value& x, const Value& y, Arena& a) {
    if (x.is_list() && y.is_int()) {
        Obj* o = a.make_list();
        for (i64 i = 0; i < y.as_int(); i++)
            o->items.insert(o->items.end(), x.as_obj()->items.begin(), x.as_obj()->items.end());
        return Value::list(o);
    }
    if (y.is_list() && x.is_int()) return value_mul(y, x, a);
    if (x.is_str() && y.is_int()) {
        i64 n = y.as_int();
        if (n < 0) n = 0;
        std::string s;
        for (i64 i = 0; i < n; i++) s += x.as_obj()->s;
        return Value::str(a.make_string(std::move(s)));
    }
    if (y.is_str() && x.is_int()) return value_mul(y, x, a);
    if (x.is_int() && y.is_int()) return Value::integer(x.as_int() * y.as_int());
    double r = (x.is_int() ? (double)x.as_int() : x.as_double()) *
               (y.is_int() ? (double)y.as_int() : y.as_double());
    return Value::real(r);
}

Value value_div(const Value& x, const Value& y, Arena& a) {
    double a_ = x.is_int() ? (double)x.as_int() : x.as_double();
    double b_ = y.is_int() ? (double)y.as_int() : y.as_double();
    if (b_ == 0.0) throw XppError("division by zero");
    return Value::real(a_ / b_);
}

Value value_mod(const Value& x, const Value& y, Arena& a) {
    if (x.is_int() && y.is_int()) {
        i64 d = y.as_int();
        if (d == 0) throw XppError("modulo by zero");
        i64 m = x.as_int() % d;
        if (m != 0 && ((m < 0) != (d < 0))) m += d;   // Python floor semantics
        return Value::integer(m);
    }
    double a_ = x.is_int() ? (double)x.as_int() : x.as_double();
    double b_ = y.is_int() ? (double)y.as_int() : y.as_double();
    if (b_ == 0.0) throw XppError("modulo by zero");
    double m = std::fmod(a_, b_);
    if (m != 0 && ((m < 0) != (b_ < 0))) m += b_;
    return Value::real(m);
}

Value value_pow(const Value& x, const Value& y, Arena& a) {
    double a_ = x.is_int() ? (double)x.as_int() : x.as_double();
    double b_ = y.is_int() ? (double)y.as_int() : y.as_double();
    return Value::real(std::pow(a_, b_));
}

// ---------------------------------------------------------------------------
// Builtins
// ---------------------------------------------------------------------------
static const std::vector<std::pair<std::string, u32>> BUILTINS = {
    {"print", 0}, {"input", 1}, {"str", 2}, {"int", 3}, {"float", 4},
    {"len", 5}, {"abs", 6}, {"min", 7}, {"max", 8}, {"sum", 9},
    {"sorted", 10}, {"range", 11}, {"type", 12}, {"bool", 13},
    {"push", 14}, {"append", 15}, {"pop", 16}, {"get", 17}, {"set", 18},
    {"contains", 19}, {"keys", 20}, {"values", 21}, {"read", 22},
    {"write", 23}, {"exit", 24}, {"clock", 25},
};

u32 builtin_id(const std::string& name) {
    for (auto& b : BUILTINS) if (b.first == name) return b.second;
    return 0xFFFFFFFFu;
}

std::string builtin_name(u32 id) {
    for (auto& b : BUILTINS) if (b.second == id) return b.first;
    return "?";
}

// helpers ------------------------------------------------------------------
static i64 require_int(const Value& v, const char* what) {
    if (!v.is_number()) throw XppError(std::string("builtin requires number for ") + what);
    return v.is_int() ? v.as_int() : (i64)v.as_double();
}

static std::istream& GLOBAL_ISTREAM = std::cin;

static Value input_one_line(Arena& a, const std::string& prompt) {
    if (!prompt.empty()) std::cout << prompt;
    std::string line;
    if (!std::getline(std::cin, line)) line = "";
    return Value::str(a.make_string(std::move(line)));
}

Value builtin_call(VM& vm, u32 id, const std::vector<Value>& args, std::string* err) {
    Arena& a = vm.arena;
    auto bad = [&](const std::string& m) -> Value {
        if (err) *err = m;
        return Value::nil();
    };
    try {
        switch (id) {
            case 0: { // print
                for (size_t i = 0; i < args.size(); i++) {
                    if (i) std::cout << " ";
                    std::cout << to_display_string(args[i], a);
                }
                std::cout << "\n";
                return Value::nil();
            }
            case 1: { // input [prompt]
                std::string p = args.empty() ? "" : (args[0].is_str() ? args[0].as_obj()->s : to_str(args[0], a));
                return input_one_line(a, p);
            }
            case 2: return Value::str(a.make_string(to_str(args.empty() ? Value::nil() : args[0], a)));
            case 3: { // int
                if (args.empty()) return bad("int() needs 1 argument");
                if (args[0].is_int()) return args[0];
                if (args[0].is_num()) return Value::integer((i64)args[0].as_double());
                if (args[0].is_str()) {
                    try { return Value::integer(std::stoll(args[0].as_obj()->s)); }
                    catch (...) { return bad("int(): invalid integer string"); }
                }
                return bad("int(): unsupported type");
            }
            case 4: { // float
                if (args.empty()) return bad("float() needs 1 argument");
                if (args[0].is_num()) return args[0];
                if (args[0].is_int()) return Value::real((double)args[0].as_int());
                if (args[0].is_str()) {
                    try {
                        size_t pos = 0;
                        double d = std::stod(args[0].as_obj()->s, &pos);
                        if (pos != args[0].as_obj()->s.size()) return bad("float(): invalid number string");
                        return Value::real(d);
                    } catch (...) { return bad("float(): invalid number string"); }
                }
                return bad("float(): unsupported type");
            }
            case 5: { // len
                if (args.empty()) return bad("len() needs 1 argument");
                if (args[0].is_str()) return Value::integer((i64)args[0].as_obj()->s.size());
                if (args[0].is_list()) return Value::integer((i64)args[0].as_obj()->items.size());
                if (args[0].is_dict()) return Value::integer((i64)args[0].as_obj()->pairs.size());
                return bad("len(): unsupported type");
            }
            case 6: { // abs
                if (args.empty()) return bad("abs() needs 1 argument");
                if (args[0].is_int()) { i64 v = args[0].as_int(); return Value::integer(v < 0 ? -v : v); }
                if (args[0].is_num()) return Value::real(std::fabs(args[0].as_double()));
                return bad("abs(): unsupported type");
            }
            case 7: case 8: { // min / max
                if (args.empty()) return bad(std::string(builtin_name(id)) + "() needs arguments");
                Value b = args[0];
                for (size_t i = 1; i < args.size(); i++) {
                    int c = value_compare(args[i], b, a);
                    if ((id == 7 && c < 0) || (id == 8 && c > 0)) b = args[i];
                }
                return b;
            }
            case 9: { // sum
                const Value& seq = args.empty() ? Value::nil() : args[0];
                if (!(seq.is_list() || seq.is_str())) return bad("sum() needs a list or string");
                i64 iv = 0; double fv = 0.0; bool is_f = false;
                auto acc = [&](const Value& v) {
                    if (!v.is_number()) throw XppError("sum(): non-number element");
                    if (!is_f && (v.is_num() || (is_f = false))) { fv += v.as_double(); is_f = true; }
                    else if (is_f) { fv += v.is_int() ? (double)v.as_int() : v.as_double(); }
                    else iv += v.as_int();
                };
                if (seq.is_list()) for (auto& v : seq.as_obj()->items) acc(v);
                else { std::string s = seq.as_obj()->s; for (char c : s) acc(Value::integer(c)); }
                return is_f ? Value::real(fv) : Value::integer(iv);
            }
            case 10: { // sorted
                if (args.empty() || !args[0].is_list()) return bad("sorted() needs a list");
                std::vector<Value> copy = args[0].as_obj()->items;
                std::sort(copy.begin(), copy.end(), [&](const Value& x, const Value& y) {
                    return value_compare(x, y, a) < 0;
                });
                Obj* o = a.make_list(); o->items = std::move(copy);
                return Value::list(o);
            }
            case 11: { // range(a[,b[,step]]) -> list
                i64 lo = 0, hi = 0, st = 1;
                if (args.size() == 1) { lo = 0; hi = require_int(args[0], "range"); }
                else if (args.size() >= 2) { lo = require_int(args[0], "range"); hi = require_int(args[1], "range"); }
                if (args.size() >= 3) st = require_int(args[2], "range");
                if (st == 0) return bad("range(): step cannot be zero");
                Obj* o = a.make_list();
                if (st > 0) for (i64 i = lo; i < hi; i += st) o->items.push_back(Value::integer(i));
                else for (i64 i = lo; i > hi; i += st) o->items.push_back(Value::integer(i));
                return Value::list(o);
            }
            case 12: { // type
                if (args.empty()) return Value::str(a.make_string("nil"));
                const Value& v = args[0];
                std::string t;
                if (v.is_nil()) t = "nil";
                else if (v.is_bool()) t = v.is_true() ? "true" : "false";
                else if (v.is_int()) t = "int";
                else if (v.is_num()) t = "float";
                else if (v.is_str()) t = "string";
                else if (v.is_list()) t = "list";
                else if (v.is_dict()) t = "dict";
                else if (v.is_func()) t = "function";
                else t = "builtin";
                return Value::str(a.make_string(std::move(t)));
            }
            case 13: return Value::boolean(args.empty() ? false : args[0].truthy());
            case 14: case 15: { // push / append
                if (args.size() < 2 || !args[0].is_list()) return bad(std::string(builtin_name(id)) + "(): expected list, value");
                args[0].as_obj()->items.push_back(args[1]);
                return args[0];
            }
            case 16: { // pop list [index]
                if (args.empty() || !args[0].is_list()) return bad("pop(): expected list");
                Obj* o = args[0].as_obj();
                if (o->items.empty()) return Value::nil();
                i64 idx = args.size() >= 2 ? require_int(args[1], "pop") : (i64)o->items.size() - 1;
                if (idx < 0) idx += (i64)o->items.size();
                if (idx < 0 || (size_t)idx >= o->items.size()) return bad("pop(): index out of range");
                Value v = o->items[(size_t)idx];
                o->items.erase(o->items.begin() + idx);
                return v;
            }
            case 17: { // get(seq, key[,default])
                if (args.size() < 2) return bad("get() needs 2-3 arguments");
                const Value& seq = args[0];
                if (seq.is_list()) {
                    i64 idx = require_int(args[1], "get");
                    if (idx < 0) idx += (i64)seq.as_obj()->items.size();
                    if (idx < 0 || (size_t)idx >= seq.as_obj()->items.size())
                        return args.size() >= 3 ? args[2] : Value::nil();
                    return seq.as_obj()->items[(size_t)idx];
                }
                if (seq.is_dict()) {
                    const std::string k = args[1].is_str() ? args[1].as_obj()->s : to_str(args[1], a);
                    for (auto& p : seq.as_obj()->pairs) if (p.first == k) return p.second;
                    return args.size() >= 3 ? args[2] : Value::nil();
                }
                return bad("get(): expected list or dict");
            }
            case 18: { // set(seq, key, value)
                if (args.size() < 3) return bad("set() needs 3 arguments");
                if (args[0].is_list()) {
                    i64 idx = require_int(args[1], "set");
                    auto& items = args[0].as_obj()->items;
                    if (idx < 0) idx += (i64)items.size();
                    if (idx < 0 || (size_t)idx >= items.size()) return bad("set(): index out of range");
                    items[(size_t)idx] = args[2];
                } else if (args[0].is_dict()) {
                    const std::string k = args[1].is_str() ? args[1].as_obj()->s : to_str(args[1], a);
                    for (auto& p : args[0].as_obj()->pairs)
                        if (p.first == k) { p.second = args[2]; return args[0]; }
                    args[0].as_obj()->pairs.push_back({k, args[2]});
                } else return bad("set(): expected list or dict");
                return args[0];
            }
            case 19: { // contains(seq, key)
                if (args.size() < 2) return bad("contains() needs 2 arguments");
                if (args[0].is_list()) {
                    for (auto& v : args[0].as_obj()->items)
                        if (value_equal(v, args[1], a)) return Value::boolean(true);
                    return Value::boolean(false);
                }
                if (args[0].is_dict()) {
                    const std::string k = args[1].is_str() ? args[1].as_obj()->s : to_str(args[1], a);
                    for (auto& p : args[0].as_obj()->pairs) if (p.first == k) return Value::boolean(true);
                    return Value::boolean(false);
                }
                if (args[0].is_str()) {
                    return Value::boolean(args[0].as_obj()->s.find(args[1].is_str() ? args[1].as_obj()->s : "") != std::string::npos);
                }
                return bad("contains(): expected list/dict/string");
            }
            case 20: case 21: { // keys / values
                if (args.empty() || !args[0].is_dict()) return bad(std::string(builtin_name(id)) + "(): expected dict");
                Obj* o = a.make_list();
                for (auto& p : args[0].as_obj()->pairs)
                    o->items.push_back(id == 20 ? Value::str(a.make_string(p.first)) : p.second);
                return Value::list(o);
            }
            case 22: { // read(path)
                if (args.empty() || !args[0].is_str()) return bad("read() needs a string path");
                std::ifstream f(args[0].as_obj()->s, std::ios::binary);
                if (!f) return bad("read(): cannot open file '" + args[0].as_obj()->s + "'");
                std::ostringstream ss; ss << f.rdbuf();
                return Value::str(a.make_string(ss.str()));
            }
            case 23: { // write(path, text)
                if (args.size() < 2 || !args[0].is_str()) return bad("write() needs (path, text)");
                std::ofstream f(args[0].as_obj()->s, std::ios::binary);
                if (!f) return bad("write(): cannot open file '" + args[0].as_obj()->s + "'");
                f << (args[1].is_str() ? args[1].as_obj()->s : to_str(args[1], a));
                return Value::nil();
            }
            case 24: { // exit(code)
                i64 c = args.empty() ? 0 : require_int(args[0], "exit");
                std::exit((int)c);
            }
            case 25: { // clock() -> seconds
                return Value::real((double)std::clock() / (double)CLOCKS_PER_SEC);
            }
        }
    } catch (const XppError& e) {
        if (err) *err = e.what();
        return Value::nil();
    } catch (const std::exception& e) {
        if (err) *err = e.what();
        return Value::nil();
    }
    return bad("unknown builtin");
}

} // namespace xpp
