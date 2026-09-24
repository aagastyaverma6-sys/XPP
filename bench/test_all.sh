#!/usr/bin/env bash
# ============================================================================
#  X++ v0.4.1 – regression test suite (ZITR VM + ZJIT native + legacy XITR)
#  Usage:  bash bench/test_all.sh        (expects repo root as cwd)
#  Golden outputs are stored in bench/golden/*.expected
# ============================================================================
set -u
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
PASS=0; FAIL=0; FAILED=()
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

ok(){ PASS=$((PASS+1)); printf "  PASS  %s\n" "$1"; }
bad(){ FAIL=$((FAIL+1)); FAILED+=("$1"); printf "  FAIL  %s\n    got: %s\n    exp: %s\n" "$1" "$2" "$3"; }

# run a snippet in a mode and capture stdout+stderr
snip(){ # $1=file  $2=mode  $3=stdin(optional)
  if [ "$2" = "ZITR" ]; then
    ./xppvm zitr "$1" 2>/dev/null
  elif [ "$2" = "ZJIT" ]; then
    python3 -m xpp_core.cli run "$1" --mode ZJIT 2>/dev/null
  else
    python3 -m xpp_core.cli run "$1" --mode "$2" 2>/dev/null
  fi
}

check(){ # $1=name  $2=file  $3=mode  $4=expected
  local out; out=$(snip "$2" "$3" 2>/dev/null)
  if [ "$out" = "$4" ]; then ok "$1 [$3]"; else bad "$1 [$3]" "$out" "$4"; fi
}

echo
echo "===== X++ v0.4.1 regression suite ====="
echo

# ---- core examples --------------------------------------------------------
check "hello"        examples/hello.xp     ZITR "Hello from X++ v0.3!"
check "fib"          examples/fib.xp       ZITR "0 0
1 1
2 1
3 2
4 3
5 5
6 8
7 13
8 21
9 34
10 55"
check "fib_fast"     examples/fib_fast.xp  ZITR "832040"
check "collections"  examples/collections.xp ZITR "1
2
3
4
caught division by zero"

check "zvib-hello"     examples/hello.xp    ZJIT "Hello from X++ v0.3!"
check "zjit-fib_fast"  examples/fib_fast.xp ZJIT "832040"
check "zjit-fib"       examples/fib.xp      ZJIT "0 0
1 1
2 1
3 2
4 3
5 5
6 8
7 13
8 21
9 34
10 55"
check "zjit-collections" examples/collections.xp ZJIT "1
2
3
4
caught division by zero"

# ---- semantics: eval order, scoping, short-circuit -----------------------
cat > "$TMP/order.xp" <<'EOF'
fn f():
  s = "a"
  s = s + "b"
  return s
end
out f()
EOF
cat > "$TMP/pushglobal.xp" <<'EOF'
lst = [1,2,3]
fn addone():
  push 99 to lst
end
addone()
out lst
EOF
cat > "$TMP/or.xp" <<'EOF'
x = 1
out x == 1 or x == 2
y = 0
out y or "fallback"
EOF
for M in ZITR ZJIT; do
  check "string-add-order"  "$TMP/order.xp"      $M "ab"
  check "push-global"       "$TMP/pushglobal.xp" $M "[1, 2, 3, 99]"
  check "or-short-circuit"  "$TMP/or.xp"         $M "true
fallback"
done

# ---- control flow ---------------------------------------------------------
cat > "$TMP/cf.xp" <<'EOF'
fn classify(n):
  if n < 0:
    return "neg"
  elif n == 0:
    return "zero"
  elif n < 10:
    return "small"
  else:
    return "big"
  end
end
out classify(-5), classify(0), classify(7), classify(99)
i = 0
acc = 0
while true:
  i = i + 1
  if i > 1000:
    break
  end
  if i % 7 == 0:
    continue
  end
  acc = acc + i
end
out "sum", acc
EOF
for M in ZITR ZJIT; do
  check "ctrl-flow" "$TMP/cf.xp" $M "neg zero small big
sum 429429"
done

# ---- recursion (mutual + deep) --------------------------------------------
cat > "$TMP/recur.xp" <<'EOF'
fn is_even(n):
  if n == 0:
    return true
  end
  return is_odd(n-1)
end
fn is_odd(n):
  if n == 0:
    return false
  end
  return is_even(n-1)
end
fn count(n):
  if n <= 0:
    return 0
  end
  return count(n-1) + 1
end
out is_even(10), is_odd(7), count(10000)
EOF
check "recursion" "$TMP/recur.xp" ZITR "true true 10000"
check "recursion-jit" "$TMP/recur.xp" ZJIT "true true 10000"

# ---- collections & builtins ----------------------------------------------
cat > "$TMP/col.xp" <<'EOF'
a = [1,2,3]
b = [4,5]
out a + b
out a * 2
out len(a), len("abc")
push 6 to a
out a, a[0], a[-1]
d = {"x": 10, "y": 20}
d["z"] = 30
out d["x"], d["z"], len(d)
p = {"name": "xpp"}
p.version = "0.4.1"
out p["version"]
out [1,2,3] == [1,2,3]
out {"k":1} == {"k":1}
out sorted([3,1,2])
out min(4,2,9), max(4,2,9), sum([1,2,3])
out contains(a, 6), contains(d, "x")
out range(3)
s = "hello"
out s[0], s[-1], s + " world", s * 2
out 7 / 2, 7 % 3, 2 ** 10
out true and 5, false or "no"
out not nil, not 0, not ""
EOF
GOLD_COL="[1, 2, 3, 4, 5]
[1, 2, 3, 1, 2, 3]
3 3
[1, 2, 3, 6] 1 6
10 30 3
0.4.1
true
true
[1, 2, 3]
2 9 6
true true
[0, 1, 2]
h o hello world hellohello
3.5 1 1024
5 no
true true true"
for M in ZITR ZJIT; do
  check "collections" "$TMP/col.xp" $M "$GOLD_COL"
done

# ---- safe/errors -----------------------------------------------------------
cat > "$TMP/safe.xp" <<'EOF'
safe:
  x = 1 / 0
fail e:
  out "caught", e
end
fn boom():
  return 1 / 0
end
safe:
  boom()
fail e2:
  out "propagated", e2
end
EOF
check "safe" "$TMP/safe.xp" ZITR "caught division by zero
propagated division by zero"
check "safe-jit" "$TMP/safe.xp" ZJIT "caught division by zero
propagated division by zero"

# ---- IO (read/in) ---------------------------------------------------------
echo "io-content" > "$TMP/io.txt"
cat > "$TMP/io.xp" <<'EOF'
s = read "<TMP>/io.txt"
out s
EOF
sed -i "s|<TMP>|$TMP|" "$TMP/io.xp"
check "read" "$TMP/io.xp" ZITR "io-content"
check "read-jit" "$TMP/io.xp" ZJIT "io-content"

# ---- recursion depth flat dispatch ----------------------------------------
cat > "$TMP/deep.xp" <<'EOF'
fn count(n):
  if n <= 0:
    return 0
  end
  return count(n-1) + 1
end
out count(20000)
EOF
check "deep-recursion" "$TMP/deep.xp" ZITR "20000"
check "deep-recursion-jit" "$TMP/deep.xp" ZJIT "20000"

# ---- comments / blanks / top-level comma out ------------------------------
cat > "$TMP/blank.xp" <<'EOF'
# header
RNM=ZITR

out 1, 2, "three"   # trailing comment
EOF
check "blanks-comments" "$TMP/blank.xp" ZITR "1 2 three"
check "blanks-comments-jit" "$TMP/blank.xp" ZJIT "1 2 three"

# ---- legacy XITR still healthy -------------------------------------------
check "legacy-XITR" examples/fib_fast.xp XITR "832040"

echo
echo "===== RESULTS: $PASS passed, $FAIL failed ====="
if [ "$FAIL" -gt 0 ]; then
  printf '  failed: %s\n' "${FAILED[@]}"
  exit 1
fi
exit 0
