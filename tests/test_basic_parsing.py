import unittest
from bpmusictransposer.musicparser import MusicParser

class TestPretokenizeParser(unittest.TestCase):
    @classmethod
    def setUp(self):
        self.maxDiff = None
        self.parser = MusicParser.parsers["BagpipeMusicWriter"]

    def _test_helper(self, test_string, exp_result):
        tune = self.parser.get_tune(test_string)
        self.assertEqual(exp_result, tune.notes)

    def test_empty(self):
        test_string = ""
        expected = []
        self._test_helper(test_string, expected)

    def test_single_notes(self):
        test_string = """LG_1 LAl_2 Bl_4 Cr_8 D_16 E_32 F_64 HG_128 HA_256"""
        expected = [
            ["note", ("LG", '1'), {}],
            ["note", ("LA", '2'), {}],
            ["note", ("B", '4'), {}],
            ["note", ("C", '8'), {}],
            ["note", ("D", '16'), {}],
            ["note", ("E", '32'), {}],
            ["note", ("F", '64'), {}],
            ["note", ("HG", '128'), {}],
            ["note", ("HA", '256'), {}]
        ]
        self._test_helper(test_string, expected)

    def test_dotted_notes(self):
        test_string = "LG_4 'lg LA_4 ''la B_4 '''b C_4 ''''c D_4 '''''d E_4 ''''''e F_4 '''''''f HG_4 ''''''''hg HA_4 '''''''''ha"
        expected = [
            ["note", ("LG", 4),  {"dot": '1'}],
            ["note", ("LA", 4),  {"dot": '2'}],
            ["note", ("B", 4),   {"dot": '3'}],
            ["note", ("C", 4),   {"dot": '4'}],
            ["note", ("D", 4),  {"dot": '5'}],
            ["note", ("E", 4),  {"dot": '6'}],
            ["note", ("F", 4),  {"dot": '7'}],
            ["note", ("HG", 4),{"dot": '8'}],
            ["note", ("HA", 4),{"dot": '9'}]
        ]
        self._test_helper(test_string, expected)

    def test_doublings(self):
        test_string = "dblg dbla dbb dbc dbd dbe dbf dbhg dbha"
        expected = [
            ["double", ("LG",), {}],
            ["double", ("LA",), {}],
            ["double", ("B",), {}],
            ["double", ("C",), {}],
            ["double", ("D",), {}],
            ["double", ("E",), {}],
            ["double", ("F",), {}],
            ["double", ("HG",), {}],
            ["double", ("HA",), {}]
        ]
        self._test_helper(test_string, expected)

    def test_half_doublings(self):
        test_string = "hdblg hdbla hdbb hdbc hdbd hdbe hdbf hdbhg hdbha"
        expected = [
            ["double", ("LG",), {"half": True}],
            ["double", ("LA",), {"half": True}],
            ["double", ("B",), {"half": True}],
            ["double", ("C",), {"half": True}],
            ["double", ("D",), {"half": True}],
            ["double", ("E",), {"half": True}],
            ["double", ("F",), {"half": True}],
            ["double", ("HG",), {"half": True}],
            ["double", ("HA",), {"half": True}]
        ]
        self._test_helper(test_string, expected)


unittest.main()
