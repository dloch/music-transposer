import unittest
from bpmusictransposer.newmusicparser import MusicParser

class TestPretokenizeParser(unittest.TestCase):
    @classmethod
    def setUp(self):
        self.maxDiff = None
        self.parser = MusicParser.parsers["BagpipeMusicWriter"]


    def _test_helper(self, func, test_string, exp_result):
        result = func(test_string)
        def cleanup(x):
            if isinstance(x, str):
                return x.strip()
            return x
        result = [x for x in map(cleanup, result) if x]
        self.assertEqual(exp_result, result)

    def test_single_simple_header(self):
        test_string = """Bagpipe Music Writer Gold:1.0"""
        expected = []
        self._test_helper(self.parser._pretokenize_parse, test_string, expected)

    def test_multiple_simple_headers(self):
        test_string = "\n".join(["Bagpipe Music Writer Gold:1.0",
        "Bagpipe Reader:1.0",
        "Bagpipe Musicworks Gold:1.0",
        "Gl_4"])
        expected = ["Gl_4"]
        self._test_helper(self.parser._pretokenize_parse, test_string, expected)

    def test_single_drop_regex_header(self):
        test_string = "Bagpipe Musicworks Gold:1.0"
        expected = []
        self._test_helper(self.parser._pretokenize_parse, test_string, expected)

    def test_multiple_drop_regex_header(self):
        test_string = "Bagpipe Musicworks Gold:1.0"
        expected = []
        self._test_helper(self.parser._pretokenize_parse, test_string, expected)

    def test_mixed_regex_headers(self):
        test_string = "\n".join(["Bagpipe Musicworks Gold:1.0", 
        "Bagpipe Reader:1.0",
        "clefc El_4"])
        expected = ["clefc El_4"]
        self._test_helper(self.parser._pretokenize_parse, test_string, expected)

    def test_expected_full_header(self):
        test_string = "\n".join([ 'Bagpipe Music Writer Gold:1.0',
			'Bagpipe Reader:1.0',
			'MIDINoteMappings,(55,57,59,60,62,64,65,67,69,57,59,61,62,64,66,67,69,71,56,58,60,61,63,65,66,68,70)',
			'FrequencyMappings,(392,440,494,523,587,659,699,784,880,440,494,554,587,659,740,784,880,988,415,466,523,554,622,699,740,831,932)',
			'InstrumentMappings,(71,71,46,34,1000,60,70)',
			'GracenoteDurations,(40,40,30,50,100,200,800,1200,250,250,250,500,200)',
			'FontSizes,(90,100,100,80,250)',
			'TuneFormat,(1,0,M,L,500,500,500,500,P,1,0)',
			'"Yo Nepali",(T,C,0,0,Times New Roman,18,600,0,1,18,0,0,0)',
			'"Lilbahadur Gurung",(M,R,0,0,Times New Roman,12,400,0,0,18,0,0,0)',
			'"6 8 Quickstep",(Y,L,0,0,Times New Roman,12,400,0,0,18,0,0,0)',
			'"Brigade of Gurkhas March Past",(F,L,0,0,Times New Roman,12,400,0,0,18,0,0,0)',
			'TuneTempo,120',
			'& sharpf sharpc  6_8'])
        expected = [('title', "Yo Nepali"),
            ('composer', "Lilbahadur Gurung"),
            ('tunetype', "6 8 Quickstep"),
			('footer', "Brigade of Gurkhas March Past"),
            ('tempo', '120'),
            '& sharpf sharpc  6_8']
        self._test_helper(self.parser._pretokenize_parse, test_string, expected)

    def test_inline_headers(self):
        test_string = "\n".join(['"P/M Terry Tully",(M,R,0,0,Times New Roman,14,400,0,0,18,0,0,0)',
            '"",(F,R,0,0,Times New Roman,10,400,0,0,18,0,0,0)',
            '& sharpf sharpc 2_4',
            'I!\'\'  gg Fr_16 El_16  ^ts B_32 "Slide",(I,L,0,0,Times New Roman,11,700,0,0,0,0,0,0) "Slide",(X,L,1000,1000,Times New Roman,12,400,0,0,0,0,0,0) "Slide",(X,L,1000,1000,Times New Roman,12,400,0,0,0,0,0,0)'
            "C_16 ^te 'c",
            ' gg Fr_16 El_16   ^ts B_32 "Slide",(X,L,1000,1000,Times New Roman,12,400,0,0,0,0,0,0)',
            "C_16 ^te 'c"
        ])
        expected = [
            ("composer", "P/M Terry Tully"),
            ("footer", ""),
            "& sharpf sharpc 2_4\nI!''  gg Fr_16 El_16  ^ts B_32",
            ("footer", "Slide"),
            ("footer", "Slide"),
            ("footer", "Slide"),
            "C_16 ^te 'c\n gg Fr_16 El_16   ^ts B_32",
            ("footer", "Slide"),
            "C_16 ^te 'c"
        ]
        self._test_helper(self.parser._pretokenize_parse, test_string, expected)

    def test_stupid_headers(self):
        '''A test of all the stupid headers that don't make sense'''
        test_string = "".join(['"DN Siegel",(M,R,0,0,Times New Roman,12,400,,0,18,0,0,0)',
            '"(c) Pipe Major William Livingstone Book 2.",(F,R,0,0,Times New\nRoman,10,400,0,0,18,0,0,0)',
            '",(F,R,0,0,Arial,12,400,0,0,18,0,0,0)',
            '40,784,880,988,415,466,523,554,622,699,740,831,932)',
            'FrequencyMappings,(370,415,466,494,554,622,659,740,831,415,466,523,554,622\n,699,740,831,932,392,440,494,523,587,659,699,784,880)',
            'MIDINoteMappings,(54,56,58,59,61,63,64,66,68,56,58,60,61,63,65,66,68,70,55\n,57,59,60,62,64,65,67,69)',
            'MIDINoteMappings,(54,56,58,59,61,63,64,66,68,56,58,60,61,63,65,66,68,70,55,5\n7,59,60,62,64,65,67,69)',
            'FrequencyMappings,(370,415,466,494,554,622,659,740,831,415,466,523,554,622,6\n99,740,831,932,392,440,494,523,587,659,699,784,880)'
            ])
        expected = [('composer', 'DN Siegel'),
            ('footer', '(c) Pipe Major William Livingstone Book 2.'),
            ('footer', '')]
        self._test_helper(self.parser._pretokenize_parse, test_string, expected)


unittest.main()
