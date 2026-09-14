# Choice Viet Nam 单机版 APK

基于 `gs-project/android/`（AGI-PM Web-APK）结构复刻的全新项目，用于 choice-project 的单机版 Android 壳。

## 与 AGI-PM 的核心差异

| 项目 | AGI-PM | Choice Viet Nam |
|------|--------|-----------------|
| 包名 | `com.agipm.app` | `com.choicevietnam.app` |
| 应用名 | AGI-PM（单语） | 三语：`CHOICE VIETNAM MANAGEMENT` / `越南 CHOICE 管理系统` / `Hệ thống quản lý CHOICE của Việt Nam` |
| Logo | AGI 五角星徽标 | 提供的 CHOICE SLATS VIET NAM SVG |
| 启动页 | 远程 URL + 离线缓存代理 | 本地 `assets/index.html`（不依赖网络） |
| 签名 | `agi-pm-release.keystore` | `choice-release.keystore` |

## 目录结构

```
choice-android/
├── app/
│   ├── build.gradle.kts
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── assets/index.html          # 内置启动页（含 SVG Logo + 三语标题）
│       ├── java/com/choicevietnam/app/MainActivity.kt
│       └── res/                       # strings-zh/strings-vi + 图标 + 主题
├── build_apk.py                       # 一键打包（自动找 Gradle + 生成 keystore）
├── build_apk.bat                      # Windows 入口
├── make_app_icons.py                  # 从 PNG 源图生成各密度 mipmap
├── choice-release.keystore            # 自动生成（首次构建）
└── README.md
```

## 打包

```bash
cd choice-android
python build_apk.py
```

或双击 `build_apk.bat`。

产物输出到 `choice-android/apk/Choice-VN-<version>-release.apk`。

## 修改图标

1. 替换根目录下的方形 Logo PNG 源图。
2. 修改 `make_app_icons.py` 顶部的 `SOURCE` 路径。
3. 运行 `python make_app_icons.py`。

## 后续扩展（单机版→联机版）

当前 `MainActivity.kt` 的 `HOME_URL` 指向 `file:///android_asset/index.html`，纯离线。
如后续 choice-project 前端产物准备好，直接把 `dist/` 内容复制到 `app/src/main/assets/`，
或把 `HOME_URL` 改成本地服务地址（如 `http://127.0.0.1:3000`）/ 局域网 IP / 域名即可。
