"""月度自动刷新入口（汇率/金属/饲料/畜禽 + 云端快照）。

由操作系统定时任务（计划任务 / cron）或 CodeBuddy automation 每月调用：
     python run_monthly_refresh.py

行为：
  1. 调用 cloudflare/build_price_snapshot.py
     - 畜禽：collect_livestock.py --seed-real --incremental --online（联网抓当月）
     - 汇率/金属/饲料：同步预热缓存，确保当月数据完整
     - 生成 price_snapshot.json 并上传到 R2
  已落库月份锁死不动，仅当数据源发布新月份时才向右延伸曲线。
"""
import subprocess, sys, datetime, os

HERE = os.path.dirname(os.path.abspath(__file__))

# pythonw.exe（无窗口模式）下 sys.stdout/stderr 为 None，print() 会直接崩溃。
# 本脚本日志已写入 _monthly_refresh.log，控制台回显仅是辅助，这里安全兜底。
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

def main():
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = os.path.join(HERE, "_monthly_refresh.log")

    # 统一由 build_price_snapshot.py 完成：畜禽/汇率/金属/饲料 采集 + 快照上传
    cmd = [sys.executable, os.path.join(HERE, "cloudflare", "build_price_snapshot.py")]
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["PYTHONUTF8"] = "1"

    print("[%s] 启动月度刷新: %s" % (stamp, " ".join(cmd)))
    with open(log, "a", encoding="utf-8") as f:
        f.write("==== %s START ====\n" % stamp)
    try:
        proc = subprocess.Popen(cmd, cwd=HERE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="replace", env=child_env,
                                bufsize=1)
        with open(log, "a", encoding="utf-8") as f:
            assert proc.stdout is not None
            for line in proc.stdout:
                print(line, end="", flush=True)   # 实时回显
                f.write(line)
        rc = proc.wait(timeout=1800)
        ok = rc == 0
        with open(log, "a", encoding="utf-8") as f:
            f.write("==== %s rc=%s ====\n" % (stamp, rc))
        print("[%s] 月度刷新%s" % (stamp, "成功" if ok else "失败(见 %s)" % log))
        return 0 if ok else 1
    except Exception as e:
        with open(log, "a", encoding="utf-8") as f:
            f.write("==== %s EXCEPTION %s ====\n" % (stamp, e))
        print("异常:", e)
        return 2

if __name__ == "__main__":
    sys.exit(main())
