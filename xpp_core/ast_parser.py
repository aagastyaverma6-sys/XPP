from lark import Lark
_grammar = r"""
?start: stmt*
?stmt: func_def | if_stmt | while_stmt | for_range | for_each | try_stmt | return_stmt | break_stmt | continue_stmt | print_stmt | push_stmt | assign_stmt | expr_stmt | NEWLINE
func_def: "fn" NAME "(" [params] ")" ":" NEWLINE block "end" NEWLINE?
params: NAME ("," NAME)*
if_stmt: "if" expr ":" NEWLINE block elif_branch* else_branch? "end" NEWLINE?
elif_branch: "elif" expr ":" NEWLINE block
else_branch: "else" ":" NEWLINE block
while_stmt: "while" expr ":" NEWLINE block "end" NEWLINE?
for_range: "loop" NAME "from" expr "to" expr ["step" expr] ":" NEWLINE block "end" NEWLINE?
for_each: "loop" NAME "in" expr ":" NEWLINE block "end" NEWLINE?
try_stmt: "safe" ":" NEWLINE block "fail" [NAME] ":" NEWLINE block "end" NEWLINE?
return_stmt: "return" [expr] NEWLINE
break_stmt: "break" NEWLINE
continue_stmt: "continue" NEWLINE
print_stmt: "out" expr_list NEWLINE
push_stmt: "push" expr "to" NAME NEWLINE
assign_stmt: lvalue "=" expr NEWLINE
?lvalue: NAME "[" expr "]" -> set_item | NAME ("." NAME)+ -> set_attr | NAME -> set_var
expr_stmt: expr NEWLINE
?expr: or_expr
?or_expr: and_expr | or_expr "or" and_expr -> or_
?and_expr: not_expr | and_expr "and" not_expr -> and_
?not_expr: "not" not_expr -> not_ | compare
?compare: sum "==" sum -> eq | sum "!=" sum -> ne | sum "<=" sum -> le | sum ">=" sum -> ge | sum "<" sum -> lt | sum ">" sum -> gt | sum
?sum: sum "+" term -> add | sum "-" term -> sub | term
?term: term "*" unary -> mul | term "/" unary -> div | term "%" unary -> mod | unary
?unary: "+" unary -> pos | "-" unary -> neg | power
?power: atom "**" unary -> pow | atom
?atom: INT -> int_ | FLOAT -> float_ | STRING -> string_ | "true" -> true_ | "false" -> false_ | "nil" -> nil_ | NAME "(" [expr_list] ")" -> call | list_lit | dict_lit | NAME "[" expr "]" -> get_item | NAME ("." NAME)+ -> get_attr | NAME -> var | "(" expr ")" | "in" [STRING] -> input_ | "read" STRING -> read_ | "len" "(" expr ")" -> len_
expr_list: expr ("," expr)*
list_lit: "[" [expr_list] "]"
dict_lit: "{" [pair ("," pair)*] "}"
pair: (STRING|NAME) ":" expr
block: stmt+
%import common.CNAME -> NAME
%import common.SIGNED_INT -> INT
%import common.SIGNED_FLOAT -> FLOAT
%import common.ESCAPED_STRING -> STRING
%import common.WS_INLINE
%ignore WS_INLINE
%ignore /#[^\n]*/
NEWLINE: /(\r?\n)+/
"""
_parser = Lark(_grammar, parser="lalr", propagate_positions=True, cache=True)
def parse(src: str):
    if not src.endswith("\n"): src += "\n"
    return _parser.parse(src.replace("\r\n","\n"))
