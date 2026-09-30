# 随包组件

此目录是本机验证候选，作为未签名个人使用候选归档。程序源码与 Qt 动态库保留独立文件，未加密或静态链接；替换库后应重新验证相容性。

| 组件 | 当前版本 | 来源与许可文本 |
| --- | --- | --- |
| CPython Windows x64 embedded | 3.12.10 | [官方发行页](https://www.python.org/downloads/release/python-31210/)；随包 `runtime/LICENSE.txt`、`licenses/Python-LICENSE.txt` |
| PySide6 / Shiboken / Qt | 6.11.2 | [Qt for Python 许可说明](https://doc.qt.io/qtforpython-6/licenses.html)；随包 `licenses/Qt-for-Python/` 与组件 metadata/licenses |
| tzdata | 2026.4 | Python tzdata；随包 metadata 中的 Apache 2.0 许可和 IANA 时区数据许可 |

Qt/PySide6 源码可从 [pyside-setup v6.11.2](https://github.com/pyside/pyside-setup/tree/v6.11.2) 与 [Qt 6.11.2 官方归档](https://download.qt.io/archive/qt/6.11/6.11.2/) 获取。候选只收集所用 Qt 模块及其 DLL 依赖，不包含 WebEngine、图表等未用模块。构建清单记录实际文件和版本。

Windows 系统 API、UCRT 与 .NET Framework 使用操作系统已有组件；不打包其他机器的系统 DLL。目标是 Windows 10/11 x64。启动器是本项目 C# 源码，构建时使用系统已有编译器；应用运行不调用编译器。

CPython 3.12.10 与当前验证环境一致。官方已发布后续安全维护版本；本候选不能作为“使用最新安全运行时”的证明。正式公开发布前须完成运行时更新方案、干净 Windows 验收及全部产品门槛。

本文件提供组件清单、许可文本与来源，不代表已经完成独立发布或完整许可审查。应用自身的对外许可与签名由用户在发布前决定。
