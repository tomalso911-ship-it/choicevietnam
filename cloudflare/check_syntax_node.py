# -*- coding: utf-8 -*-
"""
用 Node.js 做权威语法检查（真实 JS 解析器，不是正则）

把 index.html 里每个 <script> 块交给 Node 的 `new Function()` 解析，
能 100% 确认有没有语法错误。
"""
import os
import re
import sys
import json
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
HTML = os.path.join(ROOT, "index.html")

# 复用项目里的 Node
NODE = r"C:\Users\tomal\.workbuddy\binaries\node\versions\22.22.2\node.exe"
if not os.path.isfile(NODE):
    NODE = "node"

with open(HTML, "r", encoding="utf-8") as f:
    html = f.read()

blocks = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)

# 只检查内联脚本（有 src 的跳过）
inline = []
for b in blocks:
    if b.strip():
        inline.append(b)

print("=" * 62)
print("  Node.js 语法检查")
print("=" * 62)
print("  内联 script 块: %d 个" % len(inline))

checker = r"""
const fs = require('fs');
const blocks = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
let bad = 0;
blocks.forEach((code, i) => {
  try {
    // 用 Function 构造器做语法解析（不执行）
    new Function(code);
    console.log('OK   block #' + i + '  (' + code.split('\n').length + ' lines)');
  } catch (e) {
    bad++;
    console.log('FAIL block #' + i);
    console.log('     ' + (e && e.message ? e.message : String(e)));
  }
});
console.log('---');
console.log('bad=' + bad);
"""

tmp_js = os.path.join(HERE, "_syntax_check.js")
tmp_json = os.path.join(HERE, "_blocks.json")

with open(tmp_js, "w", encoding="utf-8") as f:
    f.write(checker)
with open(tmp_json, "w", encoding="utf-8") as f:
    json.dump(inline, f)

try:
    r = subprocess.run(
        [NODE, tmp_js, tmp_json],
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=120
    )
    out = (r.stdout or "") + (r.stderr or "")
    print()
    for line in out.splitlines():
        print("  " + line)
    ok = "bad=0" in out
finally:
    for p in (tmp_js, tmp_json):
        try:
            os.remove(p)
        except Exception:
            pass

print()
print("=" * 62)
print("  结果: %s" % ("全部通过，无语法错误" if ok else "存在语法错误"))
print("=" * 62)
sys.exit(0 if ok else 1)
