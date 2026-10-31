# Diagnostic and formatter module for X++ v0.4.7
import re, sys, os

def format_xpp_code(src: str) -> str:
    lines = src.replace('\r\n', '\n').split('\n')
    formatted = []
    indent_level = 0
    INDENT = '    '
    
    BLOCK_START = re.compile(r'^\s*(fn\s+\w+.*:|if\s+.*:|elif\s+.*:|else\s*:|while\s+.*:|loop\s+.*:|safe\s*:|fail(\s+\w+)?\s*:)\s*$')
    BLOCK_END = re.compile(r'^\s*(end)\b')
    BLOCK_MID = re.compile(r'^\s*(elif\s+.*:|else\s*:|fail(\s+\w+)?\s*:)\s*$')
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            formatted.append('')
            continue
            
        if stripped.startswith('#') or stripped.startswith('RNM=') or stripped.startswith('USE MODEL') or stripped.startswith('use '):
            if stripped.startswith('use ') or stripped.startswith('#'):
                formatted.append((INDENT * indent_level) + stripped)
            else:
                formatted.append(stripped)
            continue
            
        if BLOCK_END.match(stripped):
            indent_level = max(0, indent_level - 1)
            formatted.append((INDENT * indent_level) + stripped)
            continue
            
        if BLOCK_MID.match(stripped):
            lvl = max(0, indent_level - 1)
            formatted.append((INDENT * lvl) + stripped)
            continue
            
        formatted.append((INDENT * indent_level) + stripped)
        
        if BLOCK_START.match(stripped):
            indent_level += 1
            
    return '\n'.join(formatted).rstrip() + '\n'


def print_diagnostic(file_path: str, src: str, line_no: int, col_no: int, message: str, hint: str = None):
    lines = src.splitlines()
    print(f'\033[1;31merror\033[0m: {message}', file=sys.stderr)
    print(f'  --> {file_path}:{line_no}:{col_no}', file=sys.stderr)
    if 1 <= line_no <= len(lines):
        line_str = lines[line_no - 1]
        gutter = f'{line_no} | '
        print(f'\033[1;34m{gutter}\033[0m{line_str}', file=sys.stderr)
        pointer_space = ' ' * (len(gutter) + max(0, col_no - 1))
        print(f'{pointer_space}\033[1;31m^\033[0m', file=sys.stderr)
    if hint:
        print(f'  \033[1;36mhint\033[0m: {hint}', file=sys.stderr)


def check_xpp_file(file_path: str) -> bool:
    if not os.path.exists(file_path):
        print(f'\033[1;31merror\033[0m: file not found: {file_path}', file=sys.stderr)
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        src = f.read()
        
    lines = src.splitlines()
    stack = []
    has_errors = False
    
    for idx, line in enumerate(lines, 1):
        s = line.strip()
        if not s or s.startswith('#'):
            continue
            
        # check block balance
        m_start = re.match(r'^(fn|if|while|loop|safe)\b', s)
        if m_start and s.endswith(':'):
            stack.append((m_start.group(1), idx))
        elif s == 'end':
            if not stack:
                print_diagnostic(file_path, src, idx, line.find('end') + 1,
                                 'extraneous \'end\' without matching block start',
                                 hint='remove this \'end\' or check missing fn/if/while/loop block')
                has_errors = True
            else:
                stack.pop()
                
    while stack:
        kw, line_no = stack.pop()
        print_diagnostic(file_path, src, line_no, 1,
                         f'unclosed block \'{kw}\'',
                         hint=f'add matching \'end\' to close this {kw} block')
        has_errors = True
        
    if not has_errors:
        print(f"[+] Syntax OK: {file_path}")
        return True
    return False
