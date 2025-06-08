# MCP 文件系统管理器与表格分析工具

基于模型上下文协议（MCP）框架构建的安全文件系统和命令执行管理器。
该工具提供安全的文件操作和命令执行功能，具有可配置的安全约束。

**其他语言版本：[English](README.md)，[中文](README_zh.md)。**

## 功能特性

### 🗂️ 文件系统操作
- **读取文件**：支持文本和二进制文件，具有可配置的读取限制
- **写入文件**：创建或追加文件内容，自动创建目录结构
- **移动文件**：重命名和移动文件，带路径验证
- **删除文件**：安全的文件删除，包含权限检查
- **列出目录**：浏览目录内容及元数据
- **创建目录**：递归创建目录结构

### 🔧 命令执行
- **Shell 命令执行**：执行命令并控制超时
- **多 Shell 支持**：支持 bash、PowerShell、cmd 等多种 shell
- **会话管理**：跟踪和管理活跃的命令会话
- **命令阻止**：可配置的危险命令阻止列表
- **输出流式传输**：实时或完整模式读取命令输出

### 🔐 安全功能
- **路径验证**：限制文件操作到允许的目录
- **命令过滤**：阻止危险的系统命令
- **超时保护**：防止长时间运行的操作
- **权限检查**：验证文件和目录访问权限

### 📊 表格分析（开发中）

## 使用方法

### 系统要求
- Python 3.10+

### 安装配置
在您的 claude_desktop_config.json 中添加以下配置：
```json
{
  "mcpServers": {
    "desktop-commander": {
      "command": "uv",
      "args": [
        "run",
        "--config",
        "/你的/配置/路径"
      ]
    }
  }
}
```

## 配置选项

### 默认配置
系统采用安全的默认配置：

```json
{
  "blocked_commands": [
    "mkfs", "format", "mount", "umount", "fdisk", "dd", "parted",
    "diskpart", "sudo", "su", "passwd", "adduser", "useradd",
    "usermod", "groupadd", "chsh", "visudo", "shutdown", "reboot",
    "halt", "poweroff", "init", "iptables", "firewall", "netsh",
    "sfc", "bcdedit", "reg", "net", "sc", "runas", "cipher", "takeown"
  ],
  "default_shell": "bash",
  "allowed_directories": [],
  "max_read_length": 1000
}
```

### 配置参数说明

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `blocked_commands` | Array | List of commands to block | System-specific dangerous commands |
| `default_shell` | String | Default shell for command execution | `bash` (Linux/Mac), `powershell.exe` (Windows) |
| `allowed_directories` | Array | Directories accessible for file operations | `[]` (uses home directory) |
| `max_read_length` | Integer | Maximum lines to read from files | `1000` |
| `add_default_config` | Boolean | Merge with default configuration | `false` |

## API 参考

### 文件系统工具

#### `read_file_tool(path, offset=0, length=None, read_all=None)`
读取文件内容，支持分页。

**参数：**
- `path` (str)：要读取的文件路径
- `offset` (int)：起始行号（默认：0）
- `length` (int)：最大读取行数（默认：来自配置）
- `read_all` (bool)：如果为 True 则读取整个文件

**返回值：** `FileResult` 对象，包含内容、路径、MIME 类型和图片标识

#### `write_file_tool(file_path, content, mode='rewrite')`
向文件写入内容。

**参数：**
- `file_path` (str)：目标文件路径
- `content` (str)：要写入的内容
- `mode` (str)：'rewrite'（重写）或 'append'（追加）

**返回值：** `bool` - 操作成功状态

#### `move_file_tool(source, destination)`
移动/重命名文件。

**参数：**
- `source` (str)：源文件路径
- `destination` (str)：目标文件路径

**返回值：** `bool` - 操作成功状态

#### `delete_file_tool(file_path)`
删除文件。

**参数：**
- `file_path` (str)：要删除的文件路径

**返回值：** `bool` - 操作成功状态

#### `list_files_tool(directory)`
列出目录内容。

**参数：**
- `directory` (str)：要列出的目录路径

**返回值：** `list` - 文件信息对象数组

#### `create_directory_tool(directory)`
创建目录。

**参数：**
- `directory` (str)：要创建的目录路径

**返回值：** `bool` - 操作成功状态

### 命令执行工具

#### `execute_command_tool(command, timeout, shell=None)`
执行 shell 命令。

**参数：**
- `command` (str)：要执行的命令
- `timeout` (float)：执行超时时间（秒）
- `shell` (str)：要使用的 shell（可选）

**返回值：** `dict` 包含执行结果

#### `read_output_tool(pid, is_full=False)`
读取命令输出。

**参数：**
- `pid` (int)：进程 ID
- `is_full` (bool)：读取完整输出或仅新内容

**返回值：** `dict` 包含输出内容

#### `get_active_sessions_tool()`
获取活跃的命令会话。

**返回值：** `dict` 包含会话详情

#### `force_terminate_tool(pid)`
终止命令会话。

**参数：**
- `pid` (int)：要终止的进程 ID

**返回值：** `dict` 包含终止状态

### 配置工具

#### `get_config_tool()`
获取当前配置。

**返回值：** `dict` - 当前配置

#### `set_config_tool(key, value)`
设置配置值。

**参数：**
- `key` (str)：配置键
- `value`：要设置的值

**返回值：** `dict` - 更新后的配置

## 安全

### 文件系统安全
- 所有文件路径都经过规范化和验证
- 操作限制在允许的目录内
- 父目录验证防止路径遍历攻击
- 文件操作具有超时保护

### 命令执行安全
- 默认阻止危险的系统命令
- 命令解析处理复杂的 shell 语法
- 进程隔离和超时控制
- 会话管理防止资源泄漏

### 最佳实践
1. **配置允许目录**：始终设置特定的允许目录
2. **检查阻止命令**：根据您的使用场景自定义阻止命令列表
3. **设置合适的超时**：在功能性和资源保护之间找到平衡
4. **监控活跃会话**：定期清理长时间运行的进程

## 错误处理

系统提供全面的错误处理：

- **路径验证错误**：无效或受限的路径
- **权限错误**：访问权限不足
- **超时错误**：操作超过时间限制
- **文件系统错误**：磁盘空间、权限等问题
- **命令执行错误**：无效命令、进程失败

## 平台支持

### 支持的平台
- **Linux**：完全支持 bash/sh shells
- **macOS**：完全支持 bash/zsh shells
- **Windows**：完全支持 PowerShell/cmd

### Shell 支持
- Bash
- Zsh
- PowerShell
- 命令提示符（cmd）
- Fish
- 通过配置支持自定义 shell


---

**注意**：此工具提供强大的文件系统和命令执行功能。请始终根据您的环境和使用场景配置适当的安全设置。