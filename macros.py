# to run the code, use: python macros.py <name_of_input_file>

import re
import sys
from dataclasses import dataclass

level = 0
macros = {}

global error_file


@dataclass
class Macro:
    name: str
    parameters: set
    output: str
    macros: {}
    called: bool = False
    stack_level: int = 0

    def __eq__(self, other):
        if isinstance(other, Macro):
            return (self.name == other.name) and (self.parameters == other.parameters) and \
                   (self.output == other.output) and (self.macros == other.macros)
        return False

    def generate_output(self, given_parameters):
        if len(given_parameters) != len(self.parameters):
            error_msg(f'Error: Number of parameters in {self.name} is {len(self.parameters)}, '
                      f'was called with {len(given_parameters)}')
            return '\n'

        final_output = ''
        output_in_lines = self.output.splitlines()
        for line in output_in_lines:
            words = line.split()
            for key, parameter in given_parameters.items():
                full_key = '$' + key
                if full_key not in self.parameters:
                    error_msg(f'Error: Unknown parameter {key}')
                line = line.replace(full_key, parameter)

            if words[0] == '#MCALL':
                final_output += call_macro(line)
            else:
                final_output += line + '\n'
        return final_output


def error_msg(msg):
    print(msg)
    error_file.write(msg + '\n')


def check_if_name(string) -> bool:
    """
    checks if word is made up of only letters, numbers and underscores and is at least 1 character long
    :return: True if it is, False if not
    """
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, string) is not None and len(string) > 0


def strip_backslash(text: str):
    index = 0
    final_output = ''
    while index < len(text):
        if text[index] == '\\':
            index += 1
        final_output += text[index]
        index += 1
    return final_output


def generate_macro(macro_def: list) -> Macro or None:
    """
    Takes a macro definition and creates a macro
    :param macro_def: list of strings where each string is one line, first line should contain #MDEF and last #MEND
    :return: Macro DataClass or None if it cannot create
    """
    line = macro_def[0]
    words = line.split()
    # check #MDEF line
    if words[0] != '#MDEF':
        error_msg(f'Error: Expected #MDEF, found {words[0]}')
        return None
    if len(words) < 2:
        error_msg('Error: No name found for a macro.')
        return None
    if not check_if_name(words[1]):
        error_msg(f'Error: Invalid name "{words[1]}". It must be made up of only numbers, letters and/or underscores.')
        return None
    if len(words) != 2:
        error_msg(f'Error: Incorrect macro declaration: {line}')
        return None

    macro_output = ''
    inside_macros = {}
    parameters = set()
    macro = Macro(name=words[1], output='', macros=inside_macros, parameters=parameters)
    line_index = 1
    while line_index < len(macro_def):
        line = macro_def[line_index]
        words = line.split()
        if line[0] == '#':
            # if #MDEF detected, create new macro recursively
            if words[0] == '#MDEF':
                macro_def_inner = extract_def(macro_def[line_index:])
                if macro_def_inner is None:
                    error_msg(f'Error: Could not find closure on {line_index}: {line}\nOmitting.')
                    line_index += 1
                    continue
                line_index += len(macro_def_inner) - 1
                new_macro = generate_macro(macro_def_inner)
                if new_macro is None:
                    error_msg(f'Error: Could not generate macro on lines '
                              f'[{line_index - len(macro_def_inner) + 1}:{line_index}]')
                    line_index += 1
                    continue
                macro.macros[new_macro.name] = new_macro
            elif words[0] == '#MEND':
                break
            elif words[0] == '#MCALL':
                macro_output += line
        else:
            macro_output += line

        # find parameters in line and put them in a set
        key_pattern = r"(?<!\\)(\$[^ \n$]*)"
        parameters.update(re.findall(key_pattern, line))

        line_index += 1
    macro.parameters = parameters
    macro.output = macro_output
    return macro


def find_macro(root, macro_name) -> Macro:
    """
    Finds macro with the given name, if it is callable, otherwise None
    :param root: root dictionary with macros
    :param macro_name: macro name
    :return: macro with given name or None if it doesn't exist
    """
    result = Macro(name=macro_name, parameters=set(), output='', macros={})
    result.stack_level = -1
    for name_, inside_macro in root.items():
        if inside_macro.name == macro_name and inside_macro.stack_level > result.stack_level:
            result = inside_macro
        if inside_macro.called:
            new_result = find_macro(inside_macro.macros, macro_name)
            if new_result is not None and inside_macro.stack_level >= result.stack_level:
                result = new_result
    return result if result.stack_level >= 0 else None


def call_macro(macro_call_line):
    """
    Analyses line with #MCALL and outputs text to be put in output
    :param macro_call_line: line containing #MCALL and parameters
    :return: output text
    """
    global level
    words = macro_call_line.split()
    if not words[0] == '#MCALL':
        error_msg(f'Error: Macro was called but no #MCALL detected.')
        return ''
    name = words[1]
    if not check_if_name(name):
        error_msg('Error: Such macro name cannot exist.')
        return ''

    # find parameters
    parameters_dict = {}
    pattern = r'^(.*?)=(.*?)$'
    for key_val_pair in words[2:]:
        match = re.match(pattern, key_val_pair)
        if match:
            param = match.group(1)
            value = match.group(2)
            parameters_dict[param] = value

    called_macro = find_macro(macros, name)
    if called_macro is None:
        error_msg(f'Error: Macro called {name} not found.')
        return ''
    level += 1
    called_macro.called = True
    called_macro.stack_level = level
    output = called_macro.generate_output(parameters_dict)
    level -= 1
    called_macro.called = False
    called_macro.stack_level = 0
    return output


def extract_def(raw_input):
    """
    Returns definition in text
    :param raw_input: list containing lines from input, starting at #MDEF
    :return: returns a list with lines from #MDEF to its #MEND
    """
    i = 0
    balance = 0
    while i < len(raw_input):
        line = raw_input[i]
        words = line.split()
        if line[0] == '#':
            if words[0] == '#MDEF':
                balance += 1
            elif words[0] == '#MEND':
                balance -= 1
            elif words[0] != '#MCALL':
                error_msg(f'Error: Unexpected # in {words[0]}')
        i += 1
        if balance == 0:
            output = raw_input[:i]
            return output
    return None


def open_files(input_name: str):
    global error_file

    try:
        error_file = open('error_log.txt', 'w')
    except PermissionError:
        print("Error: Can't create error_log file: permission denied.")
        exit(1)
    except Exception as e:
        print("Error:", str(e))
        exit(1)

    if __name__ == '__main__' and len(sys.argv) != 2:
        error_msg("Error: There has to be exactly one command line argument containing input file name.")
        error_file.close()
        exit(1)

    output_file = None
    try:
        tmp = str(input_name[:-4]) + '_processed.txt'
        output_file = open(tmp, 'w')
    except PermissionError:
        error_msg("Error: Couldn't open output file.")
        error_file.close()
        exit(1)
    except Exception as e:
        print("Error:", str(e))
        error_file.close()
        exit(1)

    whole_input = None
    try:
        input_file = open(input_name, 'r')
        whole_input = input_file.readlines()
        input_file.close()
    except FileNotFoundError:
        error_msg("Error: Can't find a file with that name.")
        error_file.close()
        output_file.close()
        exit(1)
    except PermissionError:
        error_msg("Error: Can't open the file: permission denied.")
        error_file.close()
        output_file.close()
        exit(1)
    except Exception as e:
        print("Error:", str(e))
        error_file.close()
        output_file.close()
        exit(1)
    return whole_input, output_file


def main(input_name=None):
    global macros
    if input_name is None:
        if len(sys.argv) != 2:
            print("Error: Please input exactly one parameter.")
            return
        whole_input, output_file = open_files(sys.argv[1])
    else:
        whole_input, output_file = open_files(input_name)
    # goes through each line of input
    i = 0
    while i < len(whole_input):
        line = whole_input[i]
        words = line.split()
        if len(words) < 1:
            i += 1
            output_file.write(strip_backslash(line))
            continue
        if words[0] == '#MDEF':
            macro_def = extract_def(whole_input[i:])
            if macro_def is None:
                error_msg(f'Error: Could not find closure on {i}: {line}\nOmitting.')
                i += 1
                continue
            i += len(macro_def) - 1
            new_macro = generate_macro(macro_def)
            if new_macro is None:
                error_msg(f'Error: Could not generate macro on lines [{i - len(macro_def) + 1}:{i}]')
                i += 1
                continue
            macros[new_macro.name] = new_macro
        elif words[0] == '#MEND':
            error_msg(f'Error: Unexpected #MEND at line {i}')
        elif words[0] == '#MCALL':
            if len(words) < 2:
                error_msg(f'Error: Detected #MCALL but no arguments were given at line {i}')
            else:
                output_file.write(strip_backslash(call_macro(line)))
        elif words[0][0] == '#':
            error_msg(f'Error: Unexpected # in {words[0]}')
        else:
            output_file.write(strip_backslash(line))
        i += 1
    output_file.close()
    error_file.close()


if __name__ == '__main__':
    main()
