import logging
import shlex


def extract_base_command(command: str) -> str:
    """
    Extracts the base command from a given command string.
    
    :param command: The command string from which to extract the base command.
    :return: The base command, which is the first word in the command string.
    """    
    try:
        tokens = shlex.split(command)
        return tokens[0] if tokens else ""
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
        commands = []
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

    except Exception as e:
        logging.error(f"Error parsing command '{command}': {e}")
        return [extract_base_command(command.strip())]