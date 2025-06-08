# MCP File System Manager And Table Analysis

A secure file system and command execution manager 
built on the Model Context Protocol (MCP) framework. 
This tool provides safe file operations and command 
execution with configurable security constraints.

**Read this in other languages: [English](README.md), [中文](README_zh.md).**

## Features

### 🗂️ File System Operations
- **Read Files**: Support for text and binary files with configurable read limits
- **Write Files**: Create or append to files with automatic directory creation
- **Move Files**: Rename and relocate files with path validation
- **Delete Files**: Safe file deletion with permission checks
- **List Directories**: Browse directory contents with metadata
- **Create Directories**: Create directory structures recursively

### 🔧 Command Execution
- **Shell Command Execution**: Execute commands with timeout controls
- **Multi-Shell Support**: Works with bash, PowerShell, cmd, and other shells
- **Session Management**: Track and manage active command sessions
- **Command Blocking**: Configurable blocked commands list for security
- **Output Streaming**: Read command output in real-time or full mode

### 🔐 Security Features
- **Path Validation**: Restrict file operations to allowed directories
- **Command Filtering**: Block dangerous system commands
- **Timeout Protection**: Prevent long-running operations
- **Permission Checks**: Validate file and directory access rights

### 📊 Table Analysis(TODO)

## Usage

### Prerequisites
- Python 3.10+

### Setup
Add this entry to your claude_desktop_config.json:
```json
{
  "mcpServers": {
    "desktop-commander": {
      "command": "uv",
      "args": [
        "run",
        "--config",
        "/you/config/path"
      ]
    }
  }
}
```

## Configuration

### Default Configuration
The system comes with secure defaults:

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

### Configuration Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `blocked_commands` | Array | List of commands to block | System-specific dangerous commands |
| `default_shell` | String | Default shell for command execution | `bash` (Linux/Mac), `powershell.exe` (Windows) |
| `allowed_directories` | Array | Directories accessible for file operations | `[]` (uses home directory) |
| `max_read_length` | Integer | Maximum lines to read from files | `1000` |
| `add_default_config` | Boolean | Merge with default configuration | `false` |

## API Reference

### File System Tools

#### `read_file_tool(path, offset=0, length=None, read_all=None)`
Read file content with optional pagination.

**Parameters:**
- `path` (str): File path to read
- `offset` (int): Starting line number (default: 0)
- `length` (int): Maximum lines to read (default: from config)
- `read_all` (bool): Read entire file if True

**Returns:** `FileResult` object with content, path, MIME type, and image flag

#### `write_file_tool(file_path, content, mode='rewrite')`
Write content to a file.

**Parameters:**
- `file_path` (str): Target file path
- `content` (str): Content to write
- `mode` (str): 'rewrite' or 'append'

**Returns:** `bool` - Success status

#### `move_file_tool(source, destination)`
Move/rename a file.

**Parameters:**
- `source` (str): Source file path
- `destination` (str): Destination file path

**Returns:** `bool` - Success status

#### `delete_file_tool(file_path)`
Delete a file.

**Parameters:**
- `file_path` (str): File path to delete

**Returns:** `bool` - Success status

#### `list_files_tool(directory)`
List directory contents.

**Parameters:**
- `directory` (str): Directory path to list

**Returns:** `list` - Array of file information objects

#### `create_directory_tool(directory)`
Create a directory.

**Parameters:**
- `directory` (str): Directory path to create

**Returns:** `bool` - Success status

### Command Execution Tools

#### `execute_command_tool(command, timeout, shell=None)`
Execute a shell command.

**Parameters:**
- `command` (str): Command to execute
- `timeout` (float): Execution timeout in seconds
- `shell` (str): Shell to use (optional)

**Returns:** `dict` with execution results

#### `read_output_tool(pid, is_full=False)`
Read command output.

**Parameters:**
- `pid` (int): Process ID
- `is_full` (bool): Read full output or new only

**Returns:** `dict` with output content

#### `get_active_sessions_tool()`
Get active command sessions.

**Returns:** `dict` with session details

#### `force_terminate_tool(pid)`
Terminate a command session.

**Parameters:**
- `pid` (int): Process ID to terminate

**Returns:** `dict` with termination status

### Configuration Tools

#### `get_config_tool()`
Get current configuration.

**Returns:** `dict` - Current configuration

#### `set_config_tool(key, value)`
Set configuration value.

**Parameters:**
- `key` (str): Configuration key
- `value`: Value to set

**Returns:** `dict` - Updated configuration

## Security Considerations

### File System Security
- All file paths are normalized and validated
- Operations are restricted to allowed directories
- Parent directory validation prevents path traversal
- File operations have timeout protections

### Command Execution Security
- Dangerous system commands are blocked by default
- Command parsing handles complex shell syntax
- Process isolation and timeout controls
- Session management prevents resource leaks

### Best Practices
1. **Configure Allowed Directories**: Always set specific allowed directories
2. **Review Blocked Commands**: Customize the blocked commands list for your use case
3. **Set Appropriate Timeouts**: Balance functionality with resource protection
4. **Monitor Active Sessions**: Regular cleanup of long-running processes

## Error Handling

The system provides comprehensive error handling:

- **Path Validation Errors**: Invalid or restricted paths
- **Permission Errors**: Insufficient access rights
- **Timeout Errors**: Operations exceeding time limits
- **File System Errors**: Disk space, permissions, etc.
- **Command Execution Errors**: Invalid commands, process failures

## Platform Support

### Supported Platforms
- **Linux**: Full support with bash/sh shells
- **macOS**: Full support with bash/zsh shells
- **Windows**: Full support with PowerShell/cmd

### Shell Support
- Bash
- Zsh
- PowerShell
- Command Prompt (cmd)
- Fish
- Custom shells via configuration


## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the configuration options

---

**Note**: This tool provides powerful file system and command execution capabilities. Always configure security settings appropriate for your environment and use case.