# -*- coding: utf-8 -*-
"""计划任务入口：静默刷新价格快照（金属/饲料/畜禽）并上传 R2。

由 pythonw.exe 调用（无控制台窗口），所有输出写入
cloudflare/snapshot_cron.log，便于事后排查。

刷新内容：
  1. collect_livestock.py --seed-real --incremental  （畜禽月度增量）
  2. build_price_snapshot.py                        （金属/饲料/畜禽/汇率 → R2）
"""
import os
import sys
import io
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
CF_DIR = os.path.join(HERE, "cloudflare")
os.makedirs(CF_DIR, exist_ok=True)
LOG = os.path.join(CF_DIR, "snapshot_cron.log")

_log = io.open(LOG, "a", encoding="utf-8")
_log.write("\n" + "=" * 60 + "\n")
_log.write(time.strftime("%Y-%m-%d %H:%M:%S") + " 开始刷新价格快照\n")
_log.flush()

# 把 stdout/stderr 全部改道到日志文件（pythonw 下无控制台，必须自己落盘）
sys.stdout = _log
sys.stderr = _log

sys.path.insert(0, HERE)
sys.path.insert(0, CF_DIR)

try:
    import build_price_snapshot
    build_price_snapshot.main()
    _log.write(time.strftime("%Y-%m-%d %H:%M:%S") + " 完成\n")
except Exception:
    _log.write("异常：\n" + traceback.format_exc() + "\n")
finally:
    try:
        _log.flush()
        _log.close()
    except Exception:
        pass
