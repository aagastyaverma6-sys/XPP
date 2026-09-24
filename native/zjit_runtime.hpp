// ============================================================================
//  zjit_runtime.hpp – runtime embedded in ZJIT-generated native programs
//  X++ v0.4.1 – self-contained, no dependencies beyond libc/libstdc++.
//  This file is copied next to the generated source by the ZJIT backend.
// ============================================================================
#ifndef XPP_ZJIT_RUNTIME
#define XPP_ZJIT_RUNTIME

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <utility>
#include <cmath>
#include <algorithm>
#include <ctime>
#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <stdexcept>

namespace zj {

using i64 = std::int64_t;
using u64 = std::uint64_t;
using u32 = std::uint32_t;

struct V;
struct Obj {
    int kind = 0;          // 1 string, 2 list, 3 dict
    std::string s;
    std::vector<V> items;
    std::vector<std::pair<std::string, V>> pairs;
    explicit Obj(int k) : kind(k) {}
};

struct V {
    u64 bits = (0xFFF0ull << 48) | (0ull << 48);
    V() {}
    explicit V(double d) { std::memcpy(&bits, &d, 8); }
    explicit V(i64 i) { bits = (0xFFF0ull << 48) | (3ull << 48) | ((u64)i & 0xFFFFFFFFFFFFull); }
    static V nil() { V v; v.bits = (0xFFF0ull << 48) | (0ull << 48); return v; }
    static V boolean(bool b) { V v; v.bits = (0xFFF0ull << 48) | ((b ? 2ull : 1ull) << 48); return v; }
    static V str_obj(Obj* o) { V v; v.bits = (0xFFF0ull << 48) | (4ull << 48) | ((u64)(uintptr_t)o & 0xFFFFFFFFFFFFull); return v; }
    static V list_obj(Obj* o) { V v; v.bits = (0xFFF0ull << 48) | (5ull << 48) | ((u64)(uintptr_t)o & 0xFFFFFFFFFFFFull); return v; }
    static V dict_obj(Obj* o) { V v; v.bits = (0xFFF0ull << 48) | (6ull << 48) | ((u64)(uintptr_t)o & 0xFFFFFFFFFFFFull); return v; }
    u64 tag() const { return bits >> 48; }
    bool is_tagged() const { return tag() >= 0xFFF0; }
    bool is_nil() const { return tag() == (0xFFF0 | 0); }
    bool is_bool() const { return tag() == (0xFFF0 | 1) || tag() == (0xFFF0 | 2); }
    bool is_true() const { return tag() == (0xFFF0 | 2); }
    bool is_int() const { return tag() == (0xFFF0 | 3); }
    bool is_num() const { return !is_tagged(); }
    bool is_number() const { return is_num() || is_int(); }
    bool is_str() const { return tag() == (0xFFF0 | 4); }
    bool is_list() const { return tag() == (0xFFF0 | 5); }
    bool is_dict() const { return tag() == (0xFFF0 | 6); }
    i64 as_int() const { return (i64)((i64)(bits << 16) >> 16); }
    double as_double() const { double d; std::memcpy(&d, &bits, 8); return d; }
    Obj* as_obj() const { return (Obj*)(uintptr_t)(bits & 0xFFFFFFFFFFFFull); }
    bool truthy() const {
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
};

inline V mk_float(double v) { return V(v); }
inline V mk_int(i64 v) { return V(v); }
inline V mk_str2(const std::string& s) { Obj* o = new Obj(1); o->s = s; return V::str_obj(o); }
inline V mk_true() { return V::boolean(true); }
inline V mk_false() { return V::boolean(false); }
inline V mk_nil() { return V::nil(); }
inline V mk_list(const std::vector<V>& items) { Obj* o = new Obj(2); o->items = items; return V::list_obj(o); }
inline V mk_dict(const std::vector<std::pair<std::string, V>>& pairs) { Obj* o = new Obj(3); o->pairs = pairs; return V::dict_obj(o); }

struct Error : std::exception {
    std::string m;
    explicit Error(const std::string& s) : m(s) {}
    const char* what() const noexcept override { return m.c_str(); }
};
[[noreturn]] inline void err(const std::string& s) { throw Error(s); }

inline std::string fmt(double d) {
    if (std::isnan(d)) return "nan";
    if (std::isinf(d)) return d > 0 ? "inf" : "-inf";
    if (d == (double)(i64)d && std::fabs(d) < 9.007199254740992e15)
        return std::to_string((i64)d);
    std::ostringstream os; os << std::setprecision(15) << d; return os.str();
}
inline std::string to_str(const V& v) {
    if (v.is_nil()) return "nil";
    if (v.is_bool()) return v.is_true() ? "true" : "false";
    if (v.is_int()) return std::to_string(v.as_int());
    if (v.is_str()) return v.as_obj()->s;
    if (v.is_num()) return fmt(v.as_double());
    return "<obj>";
}
inline std::string to_display(const V& v) {
    if (v.is_list()) {
        std::string r = "[";
        for (size_t i = 0; i < v.as_obj()->items.size(); i++) {
            if (i) r += ", ";
            r += to_display(v.as_obj()->items[i]);
        }
        return r + "]";
    }
    if (v.is_dict()) {
        std::string r = "{";
        for (size_t i = 0; i < v.as_obj()->pairs.size(); i++) {
            if (i) r += ", ";
            r += "\"" + v.as_obj()->pairs[i].first + "\": " + to_display(v.as_obj()->pairs[i].second);
        }
        return r + "}";
    }
    return to_str(v);
}

template <typename... A> inline void print(A&&... a) {
    std::string sep;
    ((std::cout << sep << to_display(std::forward<A>(a)), sep = " "), ...);
    std::cout << "\n";
}

inline V eq(const V& x, const V& y) {
    if (x.is_number() && y.is_number()) {
        double a = x.is_int() ? (double)x.as_int() : x.as_double();
        double b = y.is_int() ? (double)y.as_int() : y.as_double();
        return V::boolean(a == b);
    }
    if (x.tag() != y.tag()) return V::boolean(false);
    if (x.is_str()) return V::boolean(x.as_obj()->s == y.as_obj()->s);
    if (x.is_list()) {
        const auto& a = x.as_obj()->items;
        const auto& b = y.as_obj()->items;
        if (a.size() != b.size()) return V::boolean(false);
        for (size_t i = 0; i < a.size(); i++) if (!eq(a[i], b[i]).truthy()) return V::boolean(false);
        return V::boolean(true);
    }
    if (x.is_dict()) {
        const auto& a = x.as_obj()->pairs;
        const auto& b = y.as_obj()->pairs;
        if (a.size() != b.size()) return V::boolean(false);
        for (auto& p : a) {
            bool found = false;
            for (auto& q : b)
                if (p.first == q.first) { if (!eq(p.second, q.second).truthy()) return V::boolean(false); found = true; break; }
            if (!found) return V::boolean(false);
        }
        return V::boolean(true);
    }
    return V::boolean(x.bits == y.bits);
}
inline V ne(const V& x, const V& y) { return V::boolean(!eq(x, y).truthy()); }
inline int cmp(const V& x, const V& y) {
    if (x.is_number() && y.is_number()) {
        double a = x.is_int() ? (double)x.as_int() : x.as_double();
        double b = y.is_int() ? (double)y.as_int() : y.as_double();
        return a < b ? -1 : (a > b ? 1 : 0);
    }
    if (x.is_str() && y.is_str()) {
        const std::string& a = x.as_obj()->s;
        const std::string& b = y.as_obj()->s;
        return a < b ? -1 : (a > b ? 1 : 0);
    }
    err("comparison requires numbers or strings");
}
inline V lt(const V& x, const V& y) { return V::boolean(cmp(x, y) < 0); }
inline V le(const V& x, const V& y) { return V::boolean(cmp(x, y) <= 0); }
inline V gt(const V& x, const V& y) { return V::boolean(cmp(x, y) > 0); }
inline V ge(const V& x, const V& y) { return V::boolean(cmp(x, y) >= 0); }

inline V add(const V& x, const V& y) {
    if (x.is_str() && y.is_str()) { Obj* o = new Obj(1); o->s = x.as_obj()->s + y.as_obj()->s; return V::str_obj(o); }
    if (x.is_str() || y.is_str()) {
        Obj* o = new Obj(1);
        o->s = (x.is_str() ? x.as_obj()->s : to_str(x)) + (y.is_str() ? y.as_obj()->s : to_str(y));
        return V::str_obj(o);
    }
    if (x.is_list() && y.is_list()) {
        Obj* o = new Obj(2);
        o->items = x.as_obj()->items;
        o->items.insert(o->items.end(), y.as_obj()->items.begin(), y.as_obj()->items.end());
        return V::list_obj(o);
    }
    if (x.is_int() && y.is_int()) return V(x.as_int() + y.as_int());
    double a = x.is_int() ? (double)x.as_int() : x.as_double();
    double b = y.is_int() ? (double)y.as_int() : y.as_double();
    return mk_float(a + b);
}
inline V sub(const V& x, const V& y) {
    if (x.is_int() && y.is_int()) return V(x.as_int() - y.as_int());
    double a = x.is_int() ? (double)x.as_int() : x.as_double();
    double b = y.is_int() ? (double)y.as_int() : y.as_double();
    return mk_float(a - b);
}
inline V mul(const V& x, const V& y) {
    if (x.is_int() && y.is_int()) return V(x.as_int() * y.as_int());
    if (x.is_str() && y.is_int()) {
        std::string s; i64 n = y.as_int(); if (n < 0) n = 0;
        for (i64 i = 0; i < n; i++) s += x.as_obj()->s;
        Obj* o = new Obj(1); o->s = s; return V::str_obj(o);
    }
    if (y.is_str() && x.is_int()) return mul(y, x);
    if (x.is_list() && y.is_int()) {
        Obj* o = new Obj(2);
        for (i64 i = 0; i < y.as_int(); i++) o->items.insert(o->items.end(), x.as_obj()->items.begin(), x.as_obj()->items.end());
        return V::list_obj(o);
    }
    double a = x.is_int() ? (double)x.as_int() : x.as_double();
    double b = y.is_int() ? (double)y.as_int() : y.as_double();
    return mk_float(a * b);
}
inline V div(const V& x, const V& y) {
    double a = x.is_int() ? (double)x.as_int() : x.as_double();
    double b = y.is_int() ? (double)y.as_int() : y.as_double();
    if (b == 0.0) err("division by zero");
    return mk_float(a / b);
}
inline V mod(const V& x, const V& y) {
    if (x.is_int() && y.is_int()) {
        i64 b = y.as_int(); if (b == 0) err("modulo by zero");
        i64 m = x.as_int() % b;
        if (m != 0 && ((m < 0) != (b < 0))) m += b;
        return V(m);
    }
    double a = x.is_int() ? (double)x.as_int() : x.as_double();
    double b = y.is_int() ? (double)y.as_int() : y.as_double();
    if (b == 0.0) err("modulo by zero");
    double m = std::fmod(a, b);
    if (m != 0 && ((m < 0) != (b < 0))) m += b;
    return mk_float(m);
}
inline V pow(const V& x, const V& y) {
    double a = x.is_int() ? (double)x.as_int() : x.as_double();
    double b = y.is_int() ? (double)y.as_int() : y.as_double();
    return mk_float(std::pow(a, b));
}
inline V neg(const V& x) {
    if (x.is_int()) return V(-x.as_int());
    if (x.is_num()) return mk_float(-x.as_double());
    err("unary '-' needs a number");
}
inline V not_(const V& x) { return V::boolean(!x.truthy()); }
inline bool truthy(const V& x) { return x.truthy(); }
inline bool truthy(bool b) { return b; }
inline i64 as_i(const V& x) {
    if (x.is_int()) return x.as_int();
    if (x.is_num()) return (i64)x.as_double();
    err("expected number");
}

inline i64 len(const V& x) {
    if (x.is_list()) return (i64)x.as_obj()->items.size();
    if (x.is_str()) return (i64)x.as_obj()->s.size();
    if (x.is_dict()) return (i64)x.as_obj()->pairs.size();
    err("len(): unsupported type");
}
inline V get(const V& seq, const V& key) {
    if (seq.is_list()) {
        i64 i = as_i(key);
        auto& items = seq.as_obj()->items;
        if (i < 0) i += (i64)items.size();
        if (i < 0 || (size_t)i >= items.size()) err("list index out of range");
        return items[(size_t)i];
    }
    if (seq.is_str()) {
        i64 i = as_i(key);
        const std::string& s = seq.as_obj()->s;
        if (i < 0) i += (i64)s.size();
        if (i < 0 || (size_t)i >= s.size()) err("string index out of range");
        return mk_str2(std::string(1, s[(size_t)i]));
    }
    if (seq.is_dict()) {
        std::string k = key.is_str() ? key.as_obj()->s : to_str(key);
        for (auto& p : seq.as_obj()->pairs) if (p.first == k) return p.second;
        return V::nil();
    }
    err("indexing requires list/string/dict");
}
inline V setidx(V seq, const V& key, const V& val) {
    if (seq.is_list()) {
        i64 i = as_i(key);
        auto& items = seq.as_obj()->items;
        if (i < 0) i += (i64)items.size();
        if (i < 0 || (size_t)i >= items.size()) err("list index out of range");
        items[(size_t)i] = val;
    } else if (seq.is_dict()) {
        std::string k = key.is_str() ? key.as_obj()->s : to_str(key);
        for (auto& p : seq.as_obj()->pairs) if (p.first == k) { p.second = val; return seq; }
        seq.as_obj()->pairs.push_back({k, val});
    } else err("index assignment requires list/dict");
    return seq;
}
inline V attr_get(const V& obj, const std::string& name) {
    if (!obj.is_dict()) err("attribute access requires dict");
    for (auto& p : obj.as_obj()->pairs) if (p.first == name) return p.second;
    err("dict has no key '" + name + "'");
}
inline V attr_set(V obj, const std::string& name, const V& val) {
    if (!obj.is_dict()) err("attribute assignment requires dict");
    for (auto& p : obj.as_obj()->pairs) if (p.first == name) { p.second = val; return obj; }
    obj.as_obj()->pairs.push_back({name, val});
    return obj;
}
inline V push(V lst, const V& v) {
    if (!lst.is_list()) err("push() requires a list");
    lst.as_obj()->items.push_back(v);
    return lst;
}
inline V input(const std::string& prompt) {
    if (!prompt.empty()) std::cout << prompt;
    std::string line; std::getline(std::cin, line);
    return mk_str2(line);
}
inline V readf(const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    if (!f) err("read(): cannot open file '" + path + "'");
    std::ostringstream ss; ss << f.rdbuf();
    return mk_str2(ss.str());
}
inline V writef(const std::string& path, const V& text) {
    std::ofstream f(path, std::ios::binary);
    if (!f) err("write(): cannot open file '" + path + "'");
    f << (text.is_str() ? text.as_obj()->s : to_str(text));
    return V::nil();
}
inline void print_vec(const std::vector<V>& a) {
    std::string sep;
    for (auto& v : a) { std::cout << sep << to_display(v); sep = " "; }
    std::cout << "\n";
}
inline V builtin_core(u32 id, const std::vector<V>& a) {
    switch (id) {
        case 0: print_vec(a); return V::nil();
        case 1: return input(a.empty() ? "" : (a[0].is_str() ? a[0].as_obj()->s : to_str(a[0])));
        case 2: return mk_str2(to_str(a.empty() ? V::nil() : a[0]));
        case 3: return mk_int(a[0].is_int() ? a[0].as_int() : a[0].is_num() ? (i64)a[0].as_double() : std::stoll(a[0].as_obj()->s));
        case 4: return mk_float(a[0].is_int() ? (double)a[0].as_int() : a[0].as_double());
        case 5: return V(len(a.empty() ? V::nil() : a[0]));
        case 6: return a[0].is_int() ? mk_int(a[0].as_int() < 0 ? -a[0].as_int() : a[0].as_int()) : mk_float(std::fabs(a[0].as_double()));
        case 7: case 8: {
            if (a.empty()) err(std::string("min/max needs arguments"));
            V b = a[0];
            for (size_t i = 1; i < a.size(); i++) { if ((id == 7 && lt(a[i], b).truthy()) || (id == 8 && gt(a[i], b).truthy())) b = a[i]; }
            return b;
        }
        case 9: {
            if (a.empty() || !a[0].is_list()) err("sum() needs a list");
            i64 iv = 0; double fv = 0.0; bool isf = false;
            for (auto& v : a[0].as_obj()->items) {
                if (isf || v.is_num()) { fv += v.is_int() ? (double)v.as_int() : v.as_double(); isf = true; }
                else iv += v.as_int();
            }
            return isf ? mk_float(fv) : mk_int(iv);
        }
        case 10: {
            if (a.empty() || !a[0].is_list()) err("sorted() needs a list");
            auto items = a[0].as_obj()->items;
            std::sort(items.begin(), items.end(), [](const V& x, const V& y) { return lt(x, y).truthy(); });
            return mk_list(items);
        }
        case 11: {
            i64 lo = 0, hi = 0, st = 1;
            if (a.size() == 1) hi = as_i(a[0]);
            else if (a.size() >= 2) { lo = as_i(a[0]); hi = as_i(a[1]); }
            if (a.size() >= 3) st = as_i(a[2]);
            if (st == 0) err("range(): step cannot be zero");
            Obj* o = new Obj(2);
            if (st > 0) for (i64 i = lo; i < hi; i += st) o->items.push_back(V(i));
            else for (i64 i = lo; i > hi; i += st) o->items.push_back(V(i));
            return V::list_obj(o);
        }
        case 12: {
            std::string t = a.empty() ? "nil" : a[0].is_nil() ? "nil" : a[0].is_bool() ? (a[0].is_true() ? "true" : "false") : a[0].is_int() ? "int" : a[0].is_num() ? "float" : a[0].is_str() ? "string" : a[0].is_list() ? "list" : "dict";
            return mk_str2(t);
        }
        case 13: return V::boolean(a.empty() ? false : a[0].truthy());
        case 14: case 15: return push(a[0], a[1]);
        case 16: {
            if (a.empty() || !a[0].is_list()) err("pop() needs a list");
            auto& items = a[0].as_obj()->items;
            if (items.empty()) return V::nil();
            i64 i = a.size() >= 2 ? as_i(a[1]) : (i64)items.size() - 1;
            if (i < 0) i += (i64)items.size();
            if (i < 0 || (size_t)i >= items.size()) err("pop(): index out of range");
            V v = items[(size_t)i];
            items.erase(items.begin() + i);
            return v;
        }
        case 17: return get(a[0], a[1]);
        case 18: return setidx(a[0], a[1], a[2]);
        case 19: {
            if (a[0].is_list()) { for (auto& v : a[0].as_obj()->items) if (eq(v, a[1]).truthy()) return V::boolean(true); return V::boolean(false); }
            if (a[0].is_dict()) for (auto& p : a[0].as_obj()->pairs) if (p.first == to_str(a[1])) return V::boolean(true);
            if (a[0].is_str()) return V::boolean(a[0].as_obj()->s.find(a[1].is_str() ? a[1].as_obj()->s : "") != std::string::npos);
            err("contains(): expected list/dict/string");
        }
        case 20: case 21: {
            if (a.empty() || !a[0].is_dict()) err("keys()/values() needs a dict");
            Obj* o = new Obj(2);
            for (auto& p : a[0].as_obj()->pairs) o->items.push_back(id == 20 ? mk_str2(p.first) : p.second);
            return V::list_obj(o);
        }
        case 22: return readf(a[0].as_obj()->s);
        case 23: return writef(a[0].as_obj()->s, a[1]);
        case 24: std::exit((int)as_i(a.empty() ? mk_int(0) : a[0]));
        case 25: return mk_float((double)std::clock() / (double)CLOCKS_PER_SEC);
    }
    err("unknown builtin");
}
inline V builtin(u32 id, std::initializer_list<V> a) { return builtin_core(id, std::vector<V>(a)); }

} // namespace zj
#endif // XPP_ZJIT_RUNTIME
