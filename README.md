# 小龙人手机版（Android APK）

> 一个WebView壳APP，加载小龙人PSPAI前端的手机版页面。

## 目录结构

```
xiaolongren-mobile/
├── .github/workflows/build-apk.yml   # GitHub Action自动编译
├── android/                           # Android工程
│   ├── build.gradle.kts               # 顶层构建脚本
│   ├── settings.gradle.kts
│   ├── gradle.properties
│   ├── gradlew / gradlew.bat
│   └── app/
│       ├── build.gradle.kts
│       └── src/main/
│           ├── AndroidManifest.xml
│           ├── java/.../MainActivity.kt
│           └── res/                   # 图标和主题资源
└── README.md
```

## 编译方法

1. 把 `android/` 目录内容推到GitHub
2. GitHub Action自动编译
3. 在Action页面下载 `xiaolongren-mobile-apk` 工件

## 手动编译（需要有x86电脑）

用Android Studio打开 `android/` 目录，然后 Build → Build APK。
