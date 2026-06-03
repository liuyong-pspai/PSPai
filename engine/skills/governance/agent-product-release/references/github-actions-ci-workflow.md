# GitHub Actions CI 三平台编译 — 最终可用版

> 2026-06-02 经过6轮调试（v1.0.1→v1.0.6）后的成功配置

## 最终工作配置

```yaml
name: Build & Release

on:
  push:
    tags: ['v*']

permissions:
  contents: write   # 关键！softprops/action-gh-release 必需

jobs:
  build-engine:
    strategy:
      fail-fast: false   # 一个平台失败不取消其他
      matrix:
        include:
          - name: linux-x86_64
            os: ubuntu-22.04
            sep: ":"       # Linux/macOS用冒号分隔
          - name: macos
            os: macos-14
            sep: ":"
          - name: windows
            os: windows-2022
            sep: ";"       # Windows用分号！PyInstaller语法差异
    runs-on: ${{ matrix.os }}
    defaults:
      run:
        shell: bash        # Windows也用bash，避免PowerShell路径问题
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install pyinstaller pyyaml
      - name: Build
        run: |
          cd engine
          pyinstaller --onefile --name xiaolongren-engine-${{ matrix.name }} \
            --add-data "skills${{ matrix.sep }}skills" \
            --add-data "scripts${{ matrix.sep }}scripts" \
            --add-data "pspai_search.py${{ matrix.sep }}." \
            --hidden-import yaml \
            pspai_server.py
      - name: Upload engine
        uses: softprops/action-gh-release@v2
        with:
          files: engine/dist/xiaolongren-engine-${{ matrix.name }}${{ matrix.name == 'windows' && '.exe' || '' }}

      # 开源层在Linux job里顺便打包（比独立job可靠）
      - name: Pack open-source (Linux only)
        if: matrix.name == 'linux-x86_64'
        run: |
          mkdir -p release-tmp
          cp -r UI原型 release-tmp/
          cp .env.example README.md LICENSE requirements.txt start.sh release-tmp/ 2>/dev/null || true
          cd release-tmp && tar czf ../xiaolongren-open-source.tar.gz . && cd ..
      - name: Upload open-source
        if: matrix.name == 'linux-x86_64'
        uses: softprops/action-gh-release@v2
        with:
          files: xiaolongren-open-source.tar.gz
```

## 调试历史（6轮失败→成功）

| 版本 | 问题 | 修复 |
|------|------|------|
| v1.0.1 | macOS Upload失败，Linux/Windows cancelled | 缺 `permissions: contents: write` |
| v1.0.2 | 三平台全失败 | 权限加了但没生效（格式问题） |
| v1.0.3 | Linux/macOS成功，Windows失败 | Windows `--add-data` 需 `;` 不是 `:` |
| v1.0.4 | 三平台引擎成功，开源层打包失败 | `if: always() && !cancelled()` 语法不生效 |
| v1.0.5 | 同上 | tar `--exclude` 在 GitHub runner 上报错 |
| v1.0.6 | ✅ 全部成功 | 开源层合并到Linux job，用 `mkdir + cp + tar` 替代 `tar --exclude` |

## 关键教训

1. **`permissions: contents: write`** — CI没有这个权限无法创建Release
2. **`fail-fast: false`** — 矩阵编译默认一个失败取消全部，必须关掉
3. **Windows `--add-data` 分号** — PyInstaller Windows版路径分隔符是 `;` 不是 `:`
4. **`shell: bash` on Windows** — 避免PowerShell的路径转义问题
5. **开源层打包不进独立job** — `needs + if: always()` 组合不稳定，直接在Linux构建job里附带打包最可靠
6. **tar `--exclude` 不可靠** — GitHub Actions Ubuntu runner上某些情况下报错，用 `mkdir + cp + tar` 100%可靠
