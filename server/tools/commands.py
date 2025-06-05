import logging
import os
import shlex
from typing import Any, Dict, Optional

from server.config import get_config_manager
from server.utils.terminal_manager import TerminalManager

terminal_manager = TerminalManager()

def extract_base_command(command: str) -> str:
    """
    Extracts the base command from a given command string.
    
    :param command: The command string from which to extract the base command.
    :return: The base command, which is the first word in the command string.
    """    
    try:
        tokens = shlex.split(command)
        for token in tokens:
            if '=' in token and not token.startswith('-'):
                continue
            return token
        return ""
    except ValueError as e:
        logging.error(f"Error parsing command '{command}': {e}")
        return ""
    

def extract_commands(command: str) -> list:
    """
    Extracts all commands from a given command string.
    
    :param command: The command string from which to extract commands.
    :return: A list of commands, which are the words in the command string.
    """
    try:
        separators = [";", "&&", "||", "|", "&"]
        ext_cmds = []
        i = 0
        in_quotes = False
        quotes_char = ""
        current_command = ""
        escaped = False
        length = len(command)
        while i < length:
            char = command[i]
            if escaped:
                current_command += char
                escaped = False
                i += 1
                continue
            if char == "\\":
                current_command += char
                escaped = True
                i += 1
                continue
            
            if char in ('"', "'"):
                if in_quotes and char == quotes_char:
                    in_quotes = False
                    quotes_char = ""
                elif not in_quotes:
                    in_quotes = True
                    quotes_char = char
                current_command += char
                i += 1
                continue

            if in_quotes:
                current_command += char
                i += 1
                continue
            if char == '(':
                # Handle parentheses for subcommands
                open_parens = 1
                j = i + 1
                while j < length and open_parens > 0:
                    if command[j] == '(':
                        open_parens += 1
                    elif command[j] == ')':
                        open_parens -= 1
                    j += 1
                if open_parens == 0:
                    subshell = command[i + 1:j - 1]
                    subcommands = extract_commands(subshell)
                    ext_cmds.extend(subcommands)
                    i = j
                    continue

            matched_separator = None
            for sep in separators:
                if command.startswith(sep, i):
                    matched_separator = sep
                    break
            if matched_separator:
                if current_command.strip():
                    base = extract_base_command(current_command.strip())
                    if base:
                        ext_cmds.append(base)
                current_command = ""
                i += len(matched_separator)
                continue
            current_command += char
            i += 1

        if current_command.strip():
            base = extract_base_command(current_command.strip())
            if base:
                ext_cmds.append(base)
        return list(set(ext_cmds))
    except Exception as e:
        logging.error(f"Error parsing command '{command}': {e}")
        return [extract_base_command(command.strip())]


def validate_command(command: str) -> bool:
    """
    Check if the base command allows execution.

    :param command: The command to validate.
    :return: True if the command is valid, False otherwise.
    """
    commands = extract_commands(command)
    config = get_config_manager()
    blocked_commands = config.config.get("blocked_commands", [])
    if not blocked_commands:
        return True
    for cmd in commands:
        if cmd in blocked_commands:
            logging.error(f"Command '{cmd}' is blocked.")
            return False
    return True


def get_default_shell() -> str:
    """
    Get the default shell base on the OS.
    """
    if os.name == 'nt':
        return os.environ.get('COMSPEC', 'cmd.exe')
    else:
        shell_env = os.environ.get('SHELL')
        if shell_env:
            return shell_env
        try:
            import pwd
            return pwd.getpwuid(os.getuid()).pw_shell
        except Exception:
            return '/bin/sh'
        

def execute_command(command: str, timeout: float, shell: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute a shell command, return a dict.

    :param command: The command to execute.
    :param timeout: The seconds to wait before timing out.
    :param shell: The shell to use, optional.
    :return: A dict consist of follow k-v:
        - isError (bool): Whether an error occurred.
        - type (str): The type of the return value.
        - content (str): The output of the command if successful, or an error message if not.
        - pid (int, optional): The process ID of the command.
        - isBlocked (bool, optional): Whether it was blocked due to timeout.
    """
    if not validate_command(command):
        return {
            "isError": True,
            "type": "text",
            "content": f"command is blocked: {command}"
        }
    
    shell_to_use = shell
    if not shell_to_use:
        config = get_config_manager()
        shell_to_use = config.config.get("shell","")
    if not shell_to_use:        
        shell_to_use = get_default_shell()

    try:
        result = terminal_manager.execute_command(command, timeout, shell=shell_to_use)
    except Exception as e:
        return {
            "isError": True,
            "type": "text",
            "content": f"command execute exception: {e}"
        }

    return {
        "isError": False,
        "type": "result",
        "pid": result.get("pid", -1),
        "content": result.get("output", ""),
        "isBlocked": result.get("isBlocked", False)
    }


def read_output(pid: int, is_full: bool) -> Dict[str, Any]:
    """
    Get the output of the session

    :param pid: The process ID of the command.
    :param is_full: Whether to get the full output or just the new output.
    :return: A dict consist of follow k-v:
        - isError (bool): Whether an error occurred.
        - type (str): The type of the return value.
        - content (str): The output of the command if successful, or an error message if not.
    """
    output = terminal_manager.get_new_output(pid=pid, is_full=is_full)
    if not output:
        logging.warning(f"No output found for pid: {pid}")
        return {
            "isError": True,
            "type": "text",
            "content": f"No output found for pid: {pid} or session does not exist."
        }
    return {
        "isError": False,
        "type": "text",
        "content": output
    }


def get_active_sessions() -> Dict[int, Dict[str, Any]]:
    """
    Get all active sessions.
    
    :return: A dict where keys are PIDs and values are dicts with session details.
    """
    sessions = {}
    for pid, session in terminal_manager.active_sessions.items():
        sessions[pid] = {
            "pid": pid,
            "start_time": session.start_time,
            "last_output": session.last_output,
            "all_output": session.all_output,
            "is_blocked": session.is_blocked
        }
    return sessions


def force_terminate(pid: int) -> Dict[str, Any]:
    """
    Force terminate a session by PID.
    
    :param pid: The process ID of the command to terminate.
    :return: A dict indicating success or failure of the termination.
    """
    success = terminal_manager.force_terminate(pid)
    if success:
        return {
            "isError": False,
            "type": "text",
            "content": f"Session {pid} terminated successfully."
        }
    else:
        return {
            "isError": True,
            "type": "text",
            "content": f"Failed to terminate session {pid}."
        }