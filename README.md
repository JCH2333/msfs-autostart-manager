# MSFS 自启动管理器

一个用于管理 Microsoft Flight Simulator 2020 / 2024 外部自启动程序的 Windows 图形工具。它直接读取游戏的 `exe.xml`，可以添加、编辑、启用、停用或删除自启动项。

## 支持版本

| 游戏版本 | 发行渠道 | 自动识别位置 |
| --- | --- | --- |
| MSFS 2024 | Microsoft Store / Xbox | `%LOCALAPPDATA%\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\exe.xml` |
| MSFS 2024 | Steam | `%APPDATA%\Microsoft Flight Simulator 2024\exe.xml` |
| MSFS 2020 | Microsoft Store / Xbox | `%LOCALAPPDATA%\Packages\Microsoft.FlightSimulator_8wekyb3d8bbwe\LocalCache\exe.xml` |
| MSFS 2020 | Steam | `%APPDATA%\Microsoft Flight Simulator\exe.xml` |

也可以在界面中手动选择其他位置的 `exe.xml`。

## 下载与运行

1. 在 GitHub 的 [Releases](https://github.com/JCH2333/msfs-autostart-manager/releases/latest) 页面下载 `MSFS-Autostart-Manager.exe`。
2. 关闭正在运行的 MSFS 2020 / 2024。
3. 双击 EXE，无需安装 Python。
4. 在右上角选择要管理的游戏版本和渠道。

Windows 首次运行未经代码签名的独立工具时，可能显示 SmartScreen 提示。请核对文件来自本仓库的 Release。

## 使用方法

- **添加程序**：选择 Windows 中的 `.exe`，填写显示名称和可选启动参数。
- **编辑**：双击表格中的项目，或选中后点击“编辑”。
- **启用/停用**：保留项目，并控制下次启动模拟器时是否运行。
- **打开位置**：在资源管理器中定位对应程序。
- **删除**：只从 `exe.xml` 中删除自启动项，不会删除程序文件。
- **刷新**：重新读取当前配置，适合外部安装器刚刚修改过配置的情况。

表格还会标记程序文件是否存在，便于清理已经卸载软件留下的无效项目。

## 启动参数说明

`CommandLine` 参数由对应程序的开发者定义，而不是 MSFS 的通用参数。例如 `-auto` 可能表示自动连接模拟器，`--target-distro steam` 可能表示使用 Steam 渠道。不要随意修改不熟悉的参数。

有些程序在 MSFS 启动时已经作为后台进程运行，但会等待 SimConnect 或检测到特定机模后才开始实际工作。这通常是程序自身的逻辑，不是 `exe.xml` 提供的通用“按机模启动”功能。

## 数据安全

每次写入前，工具都会在原配置旁生成带时间戳的备份：

```text
exe.xml.backup-20260729-175034-123456
```

配置使用临时文件完成写入后再替换原文件，降低写入中断造成配置损坏的风险。工具不会删除被管理的 EXE 文件。

## 从源码运行

需要 Windows 和 Python 3.10 或更高版本。程序运行本身只使用 Python 标准库。

```powershell
git clone https://github.com/JCH2333/msfs-autostart-manager.git
cd msfs-autostart-manager
python main.py
```

运行测试：

```powershell
python -m unittest discover -v
```

构建单文件 EXE：

```powershell
python -m pip install -r requirements-dev.txt
.\build.ps1
```

成品会生成在 `dist\MSFS-Autostart-Manager.exe`。

## 当前版本

`v1.1.0`
