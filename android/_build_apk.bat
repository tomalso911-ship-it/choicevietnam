@echo off
cd /d %~dp0
set JAVA_HOME=C:\Program Files\Android\Android Studio\jbr
set ANDROID_HOME=%USERPROFILE%\AppData\Local\Android\Sdk
set PATH=%JAVA_HOME%\bin;%PATH%
gradlew.bat clean assembleRelease --console=plain --stacktrace > c:\gs-project\_apk_build.log 2>&1
set RC=%ERRORLEVEL%
echo BUILD_EXIT=%RC% >> c:\gs-project\_apk_build.log
