import pytest
import filecmp
import macros


def create_names(func_name):
    return ['test_files/' + func_name + '/' + func_name + '.txt',
            'test_files/' + func_name + '/' + func_name + '_processed.txt',
            'test_files/' + func_name + '/' + func_name + '_correct.txt']


def compare_files(func_name):
    input_file, output, correct_output = create_names(func_name)
    macros.main(input_file)
    macros.macros.clear()
    try:
        with open(output, 'r') as output_file, open(correct_output, 'r') as correct_output_file:
            return filecmp.cmp(correct_output, output)
    except Exception as e:
        print("Error:", str(e))


def test_basic_functionality():
    assert compare_files('test_basic_functionality')


def test_many_the_same_names():
    assert compare_files('test_many_the_same_names')


def test_nested_call():
    assert compare_files('test_nested_call')


def test_params_with_nested_calls():
    assert compare_files('test_params_with_nested_calls')


def test_same_names_nested():
    assert compare_files('test_same_names_nested')


def test_error_macro_should_not_be_visible():
    assert compare_files('test_error_macro_should_not_be_visible')


# Run the tests
if __name__ == '__main__':
    pytest.main()
