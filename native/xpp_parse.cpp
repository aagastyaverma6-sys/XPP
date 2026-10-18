// ============================================================================
//  xpp_parse.cpp – X++ strict pseudocode parser (recursive descent, no deps)
//  X++ v0.4.1 – native VM core
// ============================================================================
#include "xpp.hpp"
#include <cctype>
#include <map>

namespace xpp {

struct Tok {
    enum K { ID, INT, FLOAT, STR, OP, NEWLINE, EOF_ } k;
    std::string text;
    double f = 0.0;      // FLOAT
    i64 i = 0;           // INT
    size_t line = 0, col = 0;
};

struct Lexer {
    const std::string& src;
    size_t pos = 0;
    size_t line = 1, col = 1;
    std::vector<Tok> toks;

    explicit Lexer(const std::string& s) : src(s) {}

    char peek(size_t off = 0) const { return pos + off < src.size() ? src[pos + off] : '\0'; }
    char get() { char c = peek(); if (c) { pos++; if (c == '\n') { line++; col = 1; } else col++; } return c; }
    [[noreturn]] void err(const std::string& m) const {
        throw XppError("line " + std::to_string(line) + ": " + m);
    }

    void run() {
        while (pos < src.size()) {
            char c = peek();
            if (c == ' ' || c == '\t' || c == '\r') { get(); continue; }
            if (c == '\n') { toks.push_back({Tok::NEWLINE, "\n", 0, 0, line, col}); get(); continue; }
            if (c == '#') { while (peek() && peek() != '\n') get(); continue; }
            if (std::isdigit((unsigned char)c)) { number(); continue; }
            if (std::isalpha((unsigned char)c) || c == '_') { ident(); continue; }
            if (c == '"' || c == '\'') { string(); continue; }
            op();
        }
        toks.push_back({Tok::EOF_, "", 0, 0, line, col});
    }

    void number() {
        size_t s = pos, sl = line, sc = col;
        while (std::isdigit((unsigned char)peek())) get();
        bool is_float = false;
        if (peek() == '.' && std::isdigit((unsigned char)peek(1))) { is_float = true; get(); while (std::isdigit((unsigned char)peek())) get(); }
        if (peek() == 'e' || peek() == 'E') {
            is_float = true; get();
            if (peek() == '+' || peek() == '-') get();
            if (!std::isdigit((unsigned char)peek())) err("bad exponent");
            while (std::isdigit((unsigned char)peek())) get();
        }
        std::string t = src.substr(s, pos - s);
        if (is_float) toks.push_back({Tok::FLOAT, t, std::stod(t), 0, sl, sc});
        else {
            try { toks.push_back({Tok::INT, t, 0, std::stoll(t), sl, sc}); }
            catch (...) { toks.push_back({Tok::FLOAT, t, std::stod(t), 0, sl, sc}); }
        }
    }

    void ident() {
        size_t s = pos, sl = line, sc = col;
        while (std::isalnum((unsigned char)peek()) || peek() == '_') get();
        toks.push_back({Tok::ID, src.substr(s, pos - s), 0, 0, sl, sc});
    }

    void string() {
        char q = get();
        std::string out; size_t sl = line, sc = col;
        while (true) {
            char c = get();
            if (c == '\0' || c == '\n') err("unterminated string");
            if (c == '\\') {
                char e = get();
                switch (e) {
                    case 'n': out += '\n'; break;
                    case 't': out += '\t'; break;
                    case 'r': out += '\r'; break;
                    case '\\': out += '\\'; break;
                    case '"': out += '"'; break;
                    case '\'': out += '\''; break;
                    case '0': out += '\0'; break;
                    default: out += e; break;
                }
                continue;
            }
            if (c == q) break;
            out += c;
        }
        toks.push_back({Tok::STR, out, 0, 0, sl, sc});
    }

    void op() {
        char c = peek();
        static const char* two[] = {"==", "!=", "<=", ">=", "**"};
        for (auto* t : two) if (peek() == t[0] && peek(1) == t[1]) { get(); get(); toks.push_back({Tok::OP, t, 0, 0, line, col}); return; }
        static const std::string chars = "()[]{}:,+-*/%<>=.";
        if (chars.find(c) != std::string::npos) { get(); toks.push_back({Tok::OP, std::string(1, c), 0, 0, line, col}); return; }
        err(std::string("unexpected character '") + c + "'");
    }
};

// ---------------------------------------------------------------------------
// Parser
// ---------------------------------------------------------------------------
struct Parser {
    std::vector<Tok> t;
    size_t p = 0;
    Program prog;

    explicit Parser(const std::string& src) {
        Lexer lx(src);
        lx.run();
        t = std::move(lx.toks);
    }

    const Tok& cur() const { return t[p]; }
    const Tok& at(size_t off) const { return t[std::min(p + off, t.size() - 1)]; }
    bool is(Tok::K k, const char* op = nullptr) const {
        if (t[p].k != k) return false;
        return op == nullptr || t[p].text == op;
    }
    bool is_op(const char* op) const { return is(Tok::OP, op); }
    bool is_id(const char* s) const { return is(Tok::ID) && t[p].text == s; }
    bool is_kw(const char* s) const { return is(Tok::ID) && t[p].text == s; }

    void next() { if (p + 1 < t.size()) p++; }
    void expect_op(const char* op) {
        if (!is_op(op)) err("expected '" + std::string(op) + "'");
        next();
    }
    void expect_id() {
        if (!is(Tok::ID)) err("expected identifier");
        next();
    }
    [[noreturn]] void err(const std::string& m) const {
        throw XppError("line " + std::to_string(t[p].line) + ": " + m + " (near '" + t[p].text + "')");
    }

    void skip_newlines() { while (is(Tok::NEWLINE)) next(); }

    Program parse() {
        skip_newlines();
        while (!is(Tok::EOF_)) {
            skip_newlines();
            if (is_kw("RNM") || is_kw("USE")) { skip_directive_line(); continue; }
            prog.stmts.push_back(parse_stmt());
            skip_newlines();
        }
        return prog;
    }

    // skip directive lines: RNM=XITR or USE MODEL "x" (until line end)
    void skip_directive_line() {
        while (!is(Tok::NEWLINE) && !is(Tok::EOF_)) next();
        if (is(Tok::NEWLINE)) next();
    }

    Stmt parse_stmt() {
        if (is_kw("fn")) return parse_fn();
        if (is_kw("if")) return parse_if();
        if (is_kw("while")) return parse_while();
        if (is_kw("loop")) return parse_loop();
        if (is_kw("safe")) return parse_safe();
        if (is_kw("return")) { next(); Stmt s; s.k = Stmt::RET_; if (!is(Tok::NEWLINE) && !is(Tok::EOF_)) s.a = parse_expr(); return s; }
        if (is_kw("break")) { next(); Stmt s; s.k = Stmt::BREAK_; return s; }
        if (is_kw("continue")) { next(); Stmt s; s.k = Stmt::CONT_; return s; }
        if (is_kw("out")) { next(); Stmt s; s.k = Stmt::OUT_; s.args.push_back(parse_expr()); while (is_op(",")) { next(); s.args.push_back(parse_expr()); } return s; }
        if (is_kw("push")) return parse_push();
        return parse_assign_or_expr();
    }

    Stmt parse_fn() {
        next(); // fn
        Stmt s; s.k = Stmt::FN_;
        if (!is(Tok::ID)) err("expected function name");
        s.name = cur().text; next();
        expect_op("(");
        if (!is_op(")")) {
            while (true) {
                if (!is(Tok::ID)) err("expected parameter name");
                s.params.push_back(cur().text); next();
                if (!is_op(",")) break;
                next();
            }
        }
        expect_op(")");
        expect_op(":");
        skip_newlines();
        while (!is_kw("end")) { s.body.push_back(parse_stmt()); skip_newlines(); }
        next(); // end
        prog.funcs.push_back({s.name, s.params, s.body, (u32)prog.funcs.size()});
        return s;
    }

    Stmt parse_if() {
        next(); // if
        Stmt s; s.k = Stmt::IF_;
        Expr cond = parse_expr();
        expect_op(":");
        skip_newlines();
        std::vector<Stmt> body;
        while (!is_kw("elif") && !is_kw("else") && !is_kw("end")) { body.push_back(parse_stmt()); skip_newlines(); }
        s.arms.push_back({cond, body});
        while (is_kw("elif")) {
            next();
            Expr c2 = parse_expr();
            expect_op(":");
            skip_newlines();
            std::vector<Stmt> b2;
            while (!is_kw("elif") && !is_kw("else") && !is_kw("end")) { b2.push_back(parse_stmt()); skip_newlines(); }
            s.arms.push_back({c2, b2});
        }
        if (is_kw("else")) {
            next(); expect_op(":");
            skip_newlines();
            while (!is_kw("end")) { s.els.push_back(parse_stmt()); skip_newlines(); }
        }
        if (!is_kw("end")) err("expected 'end' for if");
        next();
        return s;
    }

    Stmt parse_while() {
        next();
        Stmt s; s.k = Stmt::WHILE_;
        s.a = parse_expr();
        expect_op(":");
        skip_newlines();
        while (!is_kw("end")) { s.body.push_back(parse_stmt()); skip_newlines(); }
        next();
        return s;
    }

    Stmt parse_loop() {
        next();
        Stmt s;
        if (!is(Tok::ID)) err("expected loop variable");
        std::string v = cur().text; next();
        if (is_kw("from")) {
            next();
            s.k = Stmt::LOOPF_; s.name = v;
            s.a = parse_expr();
            if (!is_kw("to")) err("expected 'to'");
            next();
            s.b = parse_expr();
            if (is_kw("step")) { next(); s.step = parse_expr(); }
        } else if (is_kw("in")) {
            next();
            s.k = Stmt::LOOPX_; s.name = v;
            s.b = parse_expr();
        } else err("expected 'from' or 'in' after loop variable");
        expect_op(":");
        skip_newlines();
        while (!is_kw("end")) { s.body.push_back(parse_stmt()); skip_newlines(); }
        next();
        return s;
    }

    Stmt parse_safe() {
        next();
        Stmt s; s.k = Stmt::SAFE_;
        expect_op(":");
        skip_newlines();
        while (!is_kw("fail")) { s.body.push_back(parse_stmt()); skip_newlines(); }
        if (is_kw("fail")) {
            next();
            if (is(Tok::ID)) { s.exc = cur().text; s.has_exc = true; next(); }
            expect_op(":");
            skip_newlines();
            while (!is_kw("end")) { s.els.push_back(parse_stmt()); skip_newlines(); }
        }
        if (!is_kw("end")) err("expected 'end' for safe");
        next();
        return s;
    }

    Stmt parse_push() {
        next();
        Stmt s; s.k = Stmt::PUSH_;
        s.a = parse_expr();
        if (!is_kw("to")) err("expected 'to' in push");
        next();
        if (!is(Tok::ID)) err("expected list name");
        s.name = cur().text; next();
        return s;
    }

    Stmt parse_assign_or_expr() {
        // lookahead: [ID | ID[...] | ID.attr] =
        if (is(Tok::ID)) {
            size_t save = p;
            std::string name = cur().text; next();
            Expr idx; bool has_idx = false;
            if (is_op("[")) {
                next();
                idx = parse_expr();
                expect_op("]");
                has_idx = true;
                // attr chain after index allowed? keep simple: none
            } else if (is_op(".")) {
                // attribute name is recorded in idx by AST? use idx as attr name expr
                next();
                if (!is(Tok::ID)) err("expected attribute name after '.'");
                idx.k = Expr::STR_; idx.sval = cur().text; idx.ival = 0; next();
                has_idx = true;
            }
            if (is_op("=")) {
                next();
                Stmt s; s.k = Stmt::SET_;
                s.name = name;
                s.a = parse_expr();
                if (has_idx) s.idx = idx;
                return s;
            }
            p = save; // not an assignment; re-parse as expression statement
        }
        Stmt s; s.k = Stmt::EXPR_;
        s.a = parse_expr();
        return s;
    }

    // expressions -----------------------------------------------------------
    Expr parse_expr() { return parse_or(); }

    Expr parse_or() {
        Expr l = parse_and();
        while (is_kw("or")) {
            next();
            Expr r = parse_and();
            Expr e; e.k = Expr::BIN_; e.binop = B_OR; e.a = std::make_shared<Expr>(l); e.b = std::make_shared<Expr>(r);
            l = e;
        }
        return l;
    }

    Expr parse_and() {
        Expr l = parse_not();
        while (is_kw("and")) {
            next();
            Expr r = parse_not();
            Expr e; e.k = Expr::BIN_; e.binop = B_AND; e.a = std::make_shared<Expr>(l); e.b = std::make_shared<Expr>(r);
            l = e;
        }
        return l;
    }

    Expr parse_not() {
        if (is_kw("not")) {
            next();
            Expr e; e.k = Expr::NOT_; e.a = std::make_shared<Expr>(parse_not());
            return e;
        }
        return parse_compare();
    }

    Expr parse_compare() {
        Expr l = parse_sum();
        for (;;) {
            u32 op = 0;
            if (is_op("==")) op = B_EQ;
            else if (is_op("!=")) op = B_NE;
            else if (is_op("<=")) op = B_LE;
            else if (is_op(">=")) op = B_GE;
            else if (is_op("<")) op = B_LT;
            else if (is_op(">")) op = B_GT;
            else break;
            next();
            Expr r = parse_sum();
            Expr e; e.k = Expr::BIN_; e.binop = op; e.a = std::make_shared<Expr>(l); e.b = std::make_shared<Expr>(r);
            l = e;
        }
        return l;
    }

    Expr parse_sum() {
        Expr l = parse_term();
        for (;;) {
            u32 op = 0;
            if (is_op("+")) op = B_ADD;
            else if (is_op("-")) op = B_SUB;
            else break;
            next();
            Expr r = parse_term();
            Expr e; e.k = Expr::BIN_; e.binop = op; e.a = std::make_shared<Expr>(l); e.b = std::make_shared<Expr>(r);
            l = e;
        }
        return l;
    }

    Expr parse_term() {
        Expr l = parse_unary();
        for (;;) {
            u32 op = 0;
            if (is_op("*")) op = B_MUL;
            else if (is_op("/")) op = B_DIV;
            else if (is_op("%")) op = B_MOD;
            else break;
            next();
            Expr r = parse_unary();
            Expr e; e.k = Expr::BIN_; e.binop = op; e.a = std::make_shared<Expr>(l); e.b = std::make_shared<Expr>(r);
            l = e;
        }
        return l;
    }

    Expr parse_unary() {
        if (is_op("-")) {
            next();
            Expr e; e.k = Expr::NEG_; e.a = std::make_shared<Expr>(parse_unary());
            return e;
        }
        if (is_op("+")) { next(); return parse_unary(); }
        return parse_power();
    }

    Expr parse_power() {
        Expr l = parse_atom();
        if (is_op("**")) {
            next();
            Expr e; e.k = Expr::BIN_; e.binop = B_POW; e.a = std::make_shared<Expr>(l); e.b = std::make_shared<Expr>(parse_unary());
            return e;
        }
        return l;
    }

    Expr parse_atom() {
        if (is(Tok::INT)) { Expr e; e.k = Expr::INT_; e.ival = cur().i; next(); return e; }
        if (is(Tok::FLOAT)) { Expr e; e.k = Expr::FLOAT_; e.fval = cur().f; next(); return e; }
        if (is(Tok::STR)) { Expr e; e.k = Expr::STR_; e.sval = cur().text; next(); return e; }
        if (is_kw("true")) { next(); Expr e; e.k = Expr::TRUE_; return e; }
        if (is_kw("false")) { next(); Expr e; e.k = Expr::FALSE_; return e; }
        if (is_kw("nil")) { next(); Expr e; e.k = Expr::NIL; return e; }
        if (is_kw("in")) {
            next();
            Expr e; e.k = Expr::INPUT_;
            if (is(Tok::STR)) { e.sval = cur().text; next(); }
            return e;
        }
        if (is_kw("read")) {
            next();
            if (!is(Tok::STR)) err("expected filename after read");
            Expr e; e.k = Expr::READ_; e.sval = cur().text; next();
            return e;
        }
        if (is_kw("len") && at(1).k == Tok::OP && at(1).text == "(") {
            next(); next();
            Expr e; e.k = Expr::LEN_; e.a = std::make_shared<Expr>(parse_expr());
            expect_op(")");
            return e;
        }
        if (is_op("[")) return parse_list();
        if (is_op("{")) return parse_dict();
        if (is_op("(")) {
            next();
            Expr e = parse_expr();
            expect_op(")");
            return parse_postfix(e);
        }
        if (is(Tok::ID)) {
            std::string name = cur().text; next();
            if (is_op("(")) {
                next();
                Expr e; e.k = Expr::CALL_; e.sval = name;
                if (!is_op(")")) {
                    while (true) {
                        e.items.push_back(parse_expr());
                        if (!is_op(",")) break;
                        next();
                    }
                }
                expect_op(")");
                return parse_postfix(e);
            }
            Expr e; e.k = Expr::VAR_; e.sval = name;
            return parse_postfix(e);
        }
        err("expected expression");
    }

    Expr parse_list() {
        next(); // [
        Expr e; e.k = Expr::LIST_;
        if (!is_op("]")) {
            while (true) {
                e.items.push_back(parse_expr());
                if (!is_op(",")) break;
                next();
            }
        }
        expect_op("]");
        return parse_postfix(e);
    }

    Expr parse_dict() {
        next(); // {
        Expr e; e.k = Expr::DICT_;
        if (!is_op("}")) {
            while (true) {
                Expr k;
                if (is(Tok::STR)) { k.k = Expr::STR_; k.sval = cur().text; next(); }
                else if (is(Tok::ID)) { k.k = Expr::STR_; k.sval = cur().text; next(); }
                else err("expected dict key");
                expect_op(":");
                Expr v = parse_expr();
                e.items.push_back(k);
                e.items.push_back(v);
                if (!is_op(",")) break;
                next();
            }
        }
        expect_op("}");
        return parse_postfix(e);
    }

    Expr parse_postfix(Expr e) {
        for (;;) {
            if (is_op("[")) {
                next();
                Expr idx = parse_expr();
                expect_op("]");
                Expr n; n.k = Expr::IDX_; n.a = std::make_shared<Expr>(e); n.b = std::make_shared<Expr>(idx);
                e = n;
            } else if (is_op(".")) {
                next();
                if (!is(Tok::ID)) err("expected attribute after '.'");
                Expr n; n.k = Expr::ATTR_; n.sval = cur().text; n.a = std::make_shared<Expr>(e);
                next();
                e = n;
            } else break;
        }
        return e;
    }
};

Program parse_program(const std::string& src) {
    Parser ps(src);
    return ps.parse();
}

} // namespace xpp
