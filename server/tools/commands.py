import logging
import shlex

from server.config import get_config_manager


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
    Validates a command string to ensure it does not contain any blocked commands.

    :param command: The command string to validate.
    :return: True if the command is valid, False otherwise.
    """
    config = get_config_manager()
    blocked_commands = config.get_value("blocked_commands") or []
    if not blocked_commands:
        return True
    cmds = extract_commands(command)
    for cmd in cmds:
        if cmd in blocked_commands:
            return False
    return True


if __name__ == '__main__':
    print(
        extract_commands('''JAVA_HOME=/usr/jdk sudo rm -rf; grep "pattern" file && echo "done"''')
    )
    print(validate_command('''JAVA_HOME=/usr/jdk sudo rm -rf; grep "pattern" file && echo "done"'''))