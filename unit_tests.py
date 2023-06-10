import unittest
import macros


class MyTestCase(unittest.TestCase):
    def test_extract_def_1(self):
        init_def = ['#MDEF test1\n', 'some text\n', '#MEND\n']
        definition = macros.extract_def(init_def)
        self.assertEqual(init_def, definition)

    def test_extract_def_2(self):
        init_def = ['#MDEF test1\n', '#MEND\n', 'some other text\n']
        definition = macros.extract_def(init_def)
        self.assertEqual(init_def[:-1], definition)

    def test_extract_def_no_closure(self):
        init_def = ['#MDEF test1\n', 'some text\n', '#MDEF\n' '#MEND\n', 'some other text\n']
        definition = macros.extract_def(init_def)
        self.assertEqual(None, definition)

    def test_extract_def_definition_inside(self):
        init_def = ['#MDEF test1\n', '#MDEF test2\n', '#MEND', '#MEND\n', 'some other text\n']
        definition = macros.extract_def(init_def)
        self.assertEqual(init_def[:-1], definition)

    def test_extract_def_definition_inside2(self):
        init_def = ['#MDEF test1\n', '#MDEF test2\n', '#MEND', '#MEND\n', '#MEND\n', 'some other text\n']
        definition = macros.extract_def(init_def)
        self.assertEqual(init_def[:-2], definition)

    def setUp(self):
        try:
            self.error_file = open('error_log.txt', 'w')
            macros.error_file = self.error_file
        except PermissionError:
            print("Error: Can't create error_log file: permission denied.")
            exit(1)

        self.test_macro_inner = macros.Macro(name='test', parameters=set(), macros={}, output='in')
        self.test_macro_inner2 = macros.Macro(name='test2', parameters=set(), macros={}, output='in')
        self.test_macro = macros.Macro(name='test', parameters=set(),
                                       macros={self.test_macro_inner.name: self.test_macro_inner,
                                               self.test_macro_inner2.name: self.test_macro_inner2},
                                       output='Basic printout')

        self.macro_2 = macros.Macro(name='macro_2', parameters={'$p1', '$p2'}, macros={}, output='stuff $p2 $p1')

        self.macro_3_inner_inner = macros.Macro(name='macro_3_inner_inner', parameters=set(), macros={}, output='in')
        self.macro_3_inner = macros.Macro(name='macro_3_inner', parameters=set(),
                                          macros={self.macro_3_inner_inner.name: self.macro_3_inner_inner}, output='in')
        self.macro_3 = macros.Macro(name='macro_3', parameters=set(),
                                    macros={self.macro_3_inner.name: self.macro_3_inner},
                                    output='#MCALL test')

        # self.macro_params = macros.Macro(name='test', parameters=set('$param1', '$param2'), macros={}, output='in')

        macros.macros.update({self.test_macro.name: self.test_macro, self.macro_2.name: self.macro_2,
                              self.macro_3.name: self.macro_3})

    def test_find_macro_basic(self):
        self.assertIsNotNone(macros.find_macro(macros.macros, 'test'))
        self.assertIsNone(macros.find_macro(macros.macros, 'test2'))

    def test_find_macro_2(self):
        self.assertEqual(self.test_macro, macros.find_macro(macros.macros, 'test'))

    def test_find_macro_3(self):
        self.assertIsNone(macros.find_macro(macros.macros, 'test2'))
        macros.macros['test'].called = True
        self.assertIsNotNone(macros.find_macro(macros.macros, 'test2'))

    def test_find_macro_adv(self):
        self.test_macro_inner.stack_level = 1
        self.test_macro.called = True
        macros.macros[self.test_macro.name] = self.test_macro
        result = macros.find_macro(macros.macros, 'test')
        self.assertEqual(self.test_macro_inner, result)

    def test_generate_macro_basic(self):
        macro_def = ['#MDEF new_macro\n',
                     '1st line\n',
                     '$param1 and $param2\n',
                     '#MEND\n']
        macro_baseline = macros.Macro('new_macro', {'$param1', '$param2'}, '1st line\n$param1 and $param2\n', {})
        generated_macro = macros.generate_macro(macro_def)
        self.assertEqual(macro_baseline, generated_macro)

    def test_generate_macro_nested(self):
        macro_def = ['#MDEF new_macro\n',
                     '1st line\n',
                     '#MDEF inner\n',
                     'Lorem Ipsum $paramInner\n',
                     '#MEND\n',
                     '$param1 and $param2\n',
                     '#MEND\n']
        inner = macros.Macro('inner', {'$paramInner'}, 'Lorem Ipsum $paramInner\n', {})
        macro_baseline = macros.Macro('new_macro', {'$param1', '$param2'}, '1st line\n$param1 and $param2\n',
                                      {'inner': inner})
        generated_macro = macros.generate_macro(macro_def)
        self.assertEqual(macro_baseline, generated_macro)

    def test_generate_macro_err(self):
        macro_def = ['#MDEF\n',
                     '#MEND\n']
        generated_macro = macros.generate_macro(macro_def)
        self.assertIsNone(generated_macro)
        macro_def[0] = '#MDEF %^$\n'
        generated_macro = macros.generate_macro(macro_def)
        self.assertIsNone(generated_macro)
        macro_def[0] = '#MDEF name name2\n'
        generated_macro = macros.generate_macro(macro_def)
        self.assertIsNone(generated_macro)

    def test_call_macro_basic(self):
        call = '#MCALL macro_2 p1=uwu p2=owo'
        self.assertEqual('stuff owo uwu\n', macros.call_macro(call))

    def test_call_macro_nested(self):
        call = '#MCALL macro_3'
        self.assertEqual('Basic printout\n', macros.call_macro(call))

    def test_call_macro_err(self):
        call = '#MCALL mmmm'
        self.assertEqual('', macros.call_macro(call))

    def tearDown(self):
        self.error_file.close()


if __name__ == '__main__':
    unittest.main()
