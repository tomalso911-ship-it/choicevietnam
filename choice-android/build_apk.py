# -*- coding: utf-8 -*-
"""
Choice Viet Nam APK 一键打包脚本

用法：
    双击 build_apk.bat
    或命令行： python build_apk.py

功能：
    1. 自动生成 release keystore（不存在时）
    2. 自动查找本地已缓存的 Gradle（优先，无需联网）
    3. 先尝试离线编译，失败自动重试联网编译
    4. 编译成功后复制 APK 到 apk/ 目录
"""
import os
import sys
import glob
import shutil
import subprocess
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
DISTS = os.path.join(os.path.expanduser("~"), ".gradle", "wrapper", "dists")
APK_SRC = os.path.join(HERE, "app", "build", "outputs", "apk", "release", "app-release.apk")
APK_DST_DIR = os.path.join(HERE, "apk")


def read_version():
    p = os.path.join(HERE, "app", "build.gradle.kts")
    try:
        txt = open(p, encoding="utf-8").read()
        m = re.search(r'versionName\s*=\s*"([^"]+)"', txt)
        if m:
            return m.group(1).strip()
    except Exception as e:
        print("    [WARN] read version failed: %s" % e)
    return "V0.0.0.0"


APK_VER = read_version()
APK_DST = os.path.join(APK_DST_DIR, "Choice-VN-%s-release.apk" % APK_VER)

JAVA_HOME = r"C:\Program Files\Android\Android Studio\jbr"
ANDROID_HOME = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Android", "Sdk")

GRADLE_VER_MIN = (8, 0, 0)
GRADLE_VER_MAX = (8, 99, 99)

KEYSTORE = os.path.join(HERE, "choice-release.keystore")


def ensure_keystore():
    if os.path.isfile(KEYSTORE):
        return 0
    print("    Keystore not found, generating %s" % KEYSTORE)
    java = os.path.join(JAVA_HOME, "bin", "keytool.exe")
    if not os.path.isfile(java):
        print("    [ERROR] keytool not found: %s" % java)
        return 1
    cmd = [
        java, "-genkey",
        "-v",
        "-keystore", KEYSTORE,
        "-alias", "choice",
        "-keyalg", "RSA",
        "-keysize", "2048",
        "-validity", "10000",
        "-storepass", "choice123",
        "-keypass", "choice123",
        "-dname", "CN=Choice, OU=IT, O=Choice, L=Hanoi, ST=VN, C=VN"
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("    [ERROR] keystore generation failed:")
        print(r.stdout[-2000:] if r.stdout else "")
        print(r.stderr[-2000:] if r.stderr else "")
        return 1
    print("    Keystore generated.")
    return 0


def find_local_gradle():
    if not os.path.isdir(DISTS):
        return None
    best = None
    best_ver = (0, 0, 0)
    pattern = os.path.join(DISTS, "*", "*", "gradle-*", "bin", "gradle.bat")
    for path in glob.glob(pattern):
        name = os.path.basename(os.path.dirname(os.path.dirname(path)))
        m = re.match(r"gradle-(\d+)\.(\d+)(?:\.(\d+))?", name)
        if not m:
            continue
        ver = (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))
        if ver < GRADLE_VER_MIN or ver > GRADLE_VER_MAX:
            continue
        if ver > best_ver:
            best_ver = ver
            best = path
    return best


def run(cmd, cwd, env=None, timeout=1800):
    print("    > %s" % " ".join(cmd))
    r = subprocess.run(
        cmd, cwd=cwd, env=env,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        timeout=timeout, shell=False,
    )
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, out


def main():
    print("=" * 62)
    print("  Choice Viet Nam APK Builder")
    print("=" * 62)
    print("  version: %s   (from app/build.gradle.kts)" % APK_VER)
    print("  output:  %s" % os.path.basename(APK_DST))

    print("\n[1/5] Environment check")
    java = os.path.join(JAVA_HOME, "bin", "java.exe")
    if not os.path.isfile(java):
        print("    [ERROR] JDK not found: %s" % java)
        return 1
    print("    JDK    : %s" % JAVA_HOME)

    if not os.path.isdir(ANDROID_HOME):
        print("    [ERROR] Android SDK not found: %s" % ANDROID_HOME)
        return 1
    print("    SDK    : %s" % ANDROID_HOME)

    env = os.environ.copy()
    env["JAVA_HOME"] = JAVA_HOME
    env["ANDROID_HOME"] = ANDROID_HOME
    env["PATH"] = os.path.join(JAVA_HOME, "bin") + os.pathsep + env.get("PATH", "")

    print("\n[2/5] Keystore")
    if ensure_keystore() != 0:
        return 1

    print("\n[3/5] Choose Gradle")
    gradle = find_local_gradle()
    if gradle:
        print("    local cache: %s" % gradle)
        gradle_cmd = [gradle]
    else:
        print("    no local cache, using gradlew.bat (needs network)")
        gradle_cmd = [os.path.join(HERE, "gradlew.bat")]

    print("\n[4/5] Build release APK")
    print("    try offline first...")
    code, out = run(gradle_cmd + ["assembleRelease", "--offline", "--stacktrace", "--console=plain"],
                    cwd=HERE, env=env)

    if code != 0:
        print("    offline failed, retry online...")
        code, out = run(gradle_cmd + ["assembleRelease", "--stacktrace", "--console=plain"],
                        cwd=HERE, env=env)

    if code != 0:
        print("\n" + "=" * 62)
        print("  Build failed")
        print("=" * 62)
        print(out)
        return 1

    print("\n[5/5] Copy APK")
    if not os.path.isfile(APK_SRC):
        print("    [ERROR] build output not found: %s" % APK_SRC)
        return 1

    os.makedirs(APK_DST_DIR, exist_ok=True)
    shutil.copy2(APK_SRC, APK_DST)
    size_mb = os.path.getsize(APK_DST) / 1024 / 1024

    print("\n" + "=" * 62)
    print("  Build success")
    print("=" * 62)
    print("  file: apk\\%s (%.2f MB)" % (os.path.basename(APK_DST), size_mb))
    print("=" * 62)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.TimeoutExpired:
        print("\n[ERROR] build timeout (30 min).")
        sys.exit(1)
    except Exception as e:
        print("\n[ERROR] %s" % e)
        import traceback
        traceback.print_exc()
        sys.exit(1)
