# -*- coding: utf-8 -*-
"""
PDF → HTML 转换（单文件、双击即看）
- 用 PyMuPDF 提取带定位样式的文本层（保留标题/段落/加粗/颜色/位置）
- 提取页内图片并以 base64 嵌入（不依赖外部文件）
- 输出单文件 HTML，浏览器直接打开，可搜索、可复制、可打印
"""
import sys, io, os, re, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 用法：python pdf2html.py "D:\某文件.pdf"   （不传参数则使用下面的默认文件）
DEFAULT_PDF = r"C:\Users\tomal\OneDrive\Desktop\亚太16国畜禽价格_采集方案\Floor-reared Broiler Project_1_1.pdf"
PDF = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
OUT = os.path.splitext(PDF)[0] + ".html"

try:
    import fitz  # PyMuPDF
except ImportError:
    print("缺少 PyMuPDF，请先执行： python -m pip install pymupdf -i https://pypi.tuna.tsinghua.edu.cn/simple")
    sys.exit(1)

doc = fitz.open(PDF)
n = doc.page_count
print("pages:", n)

body_parts = []
img_count = 0
for i in range(n):
    page = doc[i]
    body_parts.append('<section class="pdf-page" id="page-%d">' % (i + 1))
    body_parts.append('<div class="page-head">%s %d / %d</div>' % ("Page", i + 1, n))
    # 文本层（保留定位样式）
    html = page.get_text("html")
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.S | re.I)
    inner = m.group(1) if m else html
    body_parts.append('<div class="text-layer">%s</div>' % inner)
    # 图片层
    for info in page.get_images(full=True):
        xref = info[0]
        try:
            d = doc.extract_image(xref)
            ext = d.get("ext", "png")
            b64 = base64.b64encode(d["image"]).decode("ascii")
            img_count += 1
            body_parts.append(
                '<figure class="pdf-fig"><img src="data:image/%s;base64,%s" alt="figure-%d"></figure>'
                % (ext, b64, img_count)
            )
        except Exception as e:
            print("  img skip:", e)
    body_parts.append('</section>')
doc.close()

tpl = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s</title>
<style>
  body{background:#f2f3f5;margin:0;padding:20px;font-family:"Segoe UI","Microsoft YaHei",Arial,sans-serif;}
  .pdf-page{position:relative;background:#fff;margin:0 auto 22px;max-width:1000px;
            box-shadow:0 2px 12px rgba(0,0,0,.12);border-radius:6px;padding:18px 16px;overflow:hidden;}
  .page-head{font-size:12px;color:#999;margin-bottom:8px;border-bottom:1px dashed #e5e5e5;padding-bottom:6px;}
  .text-layer p{margin:0;}
  .pdf-fig{margin:14px 0;text-align:center;}
  .pdf-fig img{max-width:100%%;height:auto;border:1px solid #eee;border-radius:4px;}
  @media print{body{background:#fff;} .pdf-page{box-shadow:none;margin:0;page-break-after:always;}}
</style></head>
<body>
%(body)s
</body></html>
"""
out_html = tpl % {"title": os.path.basename(PDF), "body": "\n".join(body_parts)}
with open(OUT, "w", encoding="utf-8") as f:
    f.write(out_html)

print("images:", img_count)
print("out:", OUT)
print("size(KB):", round(os.path.getsize(OUT) / 1024, 1))
