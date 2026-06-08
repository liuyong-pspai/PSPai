#!/bin/bash
set -e

# 小龙人 全功能 APK 构建脚本
# 内嵌 Python 引擎二进制 + 完整前端

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP=app-build-full
VERSION="PSP3.6-full"
ENGINE_SRC="engine/dist/xiaolongren-engine-linux-arm64"

echo "=== 🐉 小龙人全功能APK构建 $VERSION ==="
echo "引擎: $(ls -lh $ENGINE_SRC | awk '{print $5}')"

# 清理
rm -rf $APP

# 构建目录
mkdir -p $APP/app/src/main/java/com/pspai/xiaolongren
mkdir -p $APP/app/src/main/res/values
mkdir -p $APP/app/src/main/assets/public
mkdir -p $APP/app/src/main/assets/engine

# ====== 复制引擎二进制 ======
cp $ENGINE_SRC $APP/app/src/main/assets/engine/xiaolongren-engine
echo "✅ 引擎二进制已复制 ($(ls -lh $APP/app/src/main/assets/engine/xiaolongren-engine | awk '{print $5}'))"

# ====== 复制前端文件 ======
cp -r frontend/pwa/html/* $APP/app/src/main/assets/public/
cp $APP/app/src/main/assets/public/mobile.html $APP/app/src/main/assets/public/index.html
rm -f $APP/app/src/main/assets/public/server.py $APP/app/src/main/assets/public/server_8092.py $APP/app/src/main/assets/public/validate_cured.py
rm -rf $APP/app/src/main/assets/public/pyodide $APP/app/src/main/assets/public/*.bak_*
echo "✅ 前端文件已复制 ($(find $APP/app/src/main/assets/public/ -type f | wc -l)个)"

# ====== MainActivity.java ======
cat > $APP/app/src/main/java/com/pspai/xiaolongren/MainActivity.java << 'JAVAEOF'
package com.pspai.xiaolongren;

import android.os.Bundle;
import android.os.Handler;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

public class MainActivity extends android.app.Activity {
    private WebView wv;
    private Process engineProcess;
    private Handler handler = new Handler();
    private boolean engineReady = false;

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
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        
        wv.setLayerType(WebView.LAYER_TYPE_HARDWARE, null);
        
        // 启动引擎
        startEngine();
        
        // 加载前端
        wv.loadUrl("file:///android_asset/public/index.html");
    }
    
    private void startEngine() {
        try {
            File engineDir = new File(getFilesDir(), "engine");
            engineDir.mkdirs();
            
            // 从assets解压引擎
            File engineFile = new File(engineDir, "xiaolongren-engine");
            if (!engineFile.exists()) {
                InputStream is = getAssets().open("engine/xiaolongren-engine");
                OutputStream os = new FileOutputStream(engineFile);
                byte[] buf = new byte[8192];
                int len;
                while ((len = is.read(buf)) > 0) os.write(buf, 0, len);
                is.close();
                os.close();
                engineFile.setExecutable(true);
            }
            
            // 启动引擎
            ProcessBuilder pb = new ProcessBuilder(
                engineFile.getAbsolutePath(),
                "--port", "8089",
                "--host", "127.0.0.1"
            );
            pb.directory(engineDir);
            pb.environment().put("HOME", getFilesDir().getAbsolutePath());
            engineProcess = pb.start();
            
            Toast.makeText(this, "🐉 引擎启动中...", Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(this, "引擎启动失败: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (engineProcess != null) {
            engineProcess.destroy();
        }
    }
    
    @Override
    public void onBackPressed() {
        if (wv != null && wv.canGoBack()) { wv.goBack(); }
        else { super.onBackPressed(); }
    }
}
JAVAEOF
echo "✅ MainActivity.java (全功能版)"

# ====== AndroidManifest.xml ======
cat > $APP/app/src/main/AndroidManifest.xml << 'XML'
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.pspai.xiaolongren">
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.RECORD_AUDIO"/>
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS"/>
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>
    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:label="@string/app_name"
        android:usesCleartextTraffic="true"
        android:theme="@style/AppTheme"
        android:networkSecurityConfig="@xml/network_security_config">
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

# ====== 网络安全配置 ======
mkdir -p $APP/app/src/main/res/xml
cat > $APP/app/src/main/res/xml/network_security_config.xml << 'XML'
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">127.0.0.1</domain>
        <domain includeSubdomains="true">localhost</domain>
    </domain-config>
</network-security-config>
XML
echo "✅ network_security_config.xml"

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
    if [ -f mobile/android-app/res/mipmap-${d}/ic_launcher.png ]; then
        cp mobile/android-app/res/mipmap-${d}/ic_launcher.png $APP/app/src/main/res/mipmap-${d}/ic_launcher.png
        cp mobile/android-app/res/mipmap-${d}/ic_launcher_round.png $APP/app/src/main/res/mipmap-${d}/ic_launcher_round.png
    fi
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
        versionName "PSP3.6-full"
    }
    buildTypes {
        release {
            minifyEnabled false
        }
    }
    aaptOptions {
        noCompress 'so', 'engine'
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
echo "=== 开始构建全功能APK ==="
cd $APP
gradle assembleDebug --no-daemon 2>&1 | tail -20

APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
if [ -f "$APK_PATH" ]; then
    cp "$APK_PATH" "$SCRIPT_DIR/release/$VERSION.apk"
    echo ""
    echo "=== 🎉 全功能APK构建成功！==="
    echo "输出: release/$VERSION.apk"
    echo "大小: $(ls -lh "$SCRIPT_DIR/release/$VERSION.apk" | awk '{print $5}')"
else
    echo "=== ❌ 构建失败 ==="
    exit 1
fi
