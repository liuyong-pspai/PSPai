#!/bin/bash
set -e

# 小龙人 APK 本地构建脚本 (DGX aarch64)
# 用法: bash build-apk-local.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ====== 配置 ======
# JAVA_HOME set by environment or auto-detect
if [ -z "$JAVA_HOME" ]; then
    for d in /usr/lib/jvm/java-17-openjdk-* /usr/lib/jvm/java-11-openjdk-* ~/tools/jdk-* /usr/lib/jvm/*; do
        if [ -f "$d/bin/java" ]; then
            export JAVA_HOME="$d"
            break
        fi
    done
fi
export PATH=$JAVA_HOME/bin:/opt/gradle-8.5/bin:/usr/local/bin:$PATH
export ANDROID_HOME=/opt/android-sdk
export ANDROID_SDK_ROOT=/opt/android-sdk

APP=app-build
VERSION="PSP3.6"

echo "=== 🐉 构建小龙人 APK $VERSION ==="
echo "JAVA: $(java -version 2>&1 | head -1)"
echo "Gradle: $(gradle --version 2>&1 | grep 'Gradle ' | head -1)"
echo "SDK: $ANDROID_HOME"

# ====== 清理旧构建 ======
rm -rf $APP

# ====== 构建目录结构 ======
mkdir -p $APP/app/src/main/java/com/pspai/xiaolongren
mkdir -p $APP/app/src/main/res/values
mkdir -p $APP/app/src/main/assets/public
mkdir -p $APP/app/src/main/res/drawable

# ====== 复制Web文件 ======
cp -r frontend/pwa/html/* $APP/app/src/main/assets/public/
cp $APP/app/src/main/assets/public/mobile.html $APP/app/src/main/assets/public/index.html
rm -f $APP/app/src/main/assets/public/server.py

echo "✅ Web文件已复制 ($(ls $APP/app/src/main/assets/public/ | wc -l)个)"

# ====== MainActivity.java ======
cat > $APP/app/src/main/java/com/pspai/xiaolongren/MainActivity.java << 'JAVAEOF'
package com.pspai.xiaolongren;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
public class MainActivity extends android.app.Activity {
    private WebView wv;
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        wv = new WebView(this);
        setContentView(wv);
        WebSettings s = wv.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowFileAccessFromFileURLs(true);
        s.setAllowUniversalAccessFromFileURLs(true);
        s.setCacheMode(WebSettings.LOAD_NO_CACHE);
        // 鸿蒙兼容: 硬件加速
        wv.setLayerType(WebView.LAYER_TYPE_HARDWARE, null);
        wv.setWebViewClient(new WebViewClient());
        wv.loadUrl("file:///android_asset/public/index.html");
    }
    @Override
    public void onBackPressed() {
        if (wv != null && wv.canGoBack()) { wv.goBack(); }
        else { super.onBackPressed(); }
    }
}
JAVAEOF

echo "✅ MainActivity.java"

# ====== AndroidManifest.xml ======
cat > $APP/app/src/main/AndroidManifest.xml << 'XML'
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.pspai.xiaolongren">
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.RECORD_AUDIO"/>
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS"/>
    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:label="@string/app_name"
        android:usesCleartextTraffic="true"
        android:theme="@style/AppTheme">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>
XML

echo "✅ AndroidManifest.xml"

# ====== Resources ======
cat > $APP/app/src/main/res/values/strings.xml << 'XML'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">小龙人</string>
</resources>
XML

cat > $APP/app/src/main/res/values/themes.xml << 'XML'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme" parent="android:Theme.Material.NoActionBar">
        <item name="android:windowFullscreen">true</item>
    </style>
</resources>
XML

echo "✅ Resources"

# ====== 图标 ======
for d in mdpi hdpi xhdpi xxhdpi xxxhdpi; do
    mkdir -p $APP/app/src/main/res/mipmap-${d}
    cp mobile/android-app/res/mipmap-${d}/ic_launcher.png $APP/app/src/main/res/mipmap-${d}/ic_launcher.png
    cp mobile/android-app/res/mipmap-${d}/ic_launcher_round.png $APP/app/src/main/res/mipmap-${d}/ic_launcher_round.png
done
echo "✅ 图标已复制"

# ====== build.gradle ======
cat > $APP/build.gradle << 'XML'
buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath "com.android.tools.build:gradle:8.2.0"
    }
}
allprojects {
    repositories {
        google()
        mavenCentral()
    }
}
XML

cat > $APP/app/build.gradle << 'XML'
apply plugin: "com.android.application"
android {
    namespace "com.pspai.xiaolongren"
    compileSdk 34
    defaultConfig {
        applicationId "com.pspai.xiaolongren"
        minSdk 23
        targetSdk 34
        versionCode 1
        versionName "PSP3.6"
    }
    buildTypes {
        release {
            minifyEnabled false
        }
    }
}
XML

cat > $APP/settings.gradle << 'XML'
include ":app"
rootProject.name = "XiaoLongRen"
XML

cat > $APP/gradle.properties << 'XML'
org.gradle.jvmargs=-Xmx4g
XML

echo "✅ Gradle配置"

# ====== 构建 ======
echo "=== 开始构建 ==="
cd $APP
gradle assembleDebug --no-daemon 2>&1 | tail -30

# ====== 检查结果 ======
APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
if [ -f "$APK_PATH" ]; then
    cp "$APK_PATH" "$SCRIPT_DIR/release/$VERSION.apk"
    echo ""
    echo "=== 🎉 APK构建成功！==="
    echo "输出: release/$VERSION.apk"
    echo "大小: $(ls -lh "$SCRIPT_DIR/release/$VERSION.apk" | awk '{print $5}')"
    echo "md5: $(md5sum "$SCRIPT_DIR/release/$VERSION.apk" | cut -d' ' -f1)"
else
    echo "=== ❌ 构建失败，APK未生成 ==="
    exit 1
fi
