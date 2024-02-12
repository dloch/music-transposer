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

    def test_space(self):
        test_string = "space"
        expected = [
            ["_ignore", (), {}]
        ]
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
            ["note", ("LG", '4'),  {"dot": 1}],
            ["note", ("LA", '4'),  {"dot": 2}],
            ["note", ("B", '4'),   {"dot": 3}],
            ["note", ("C", '4'),   {"dot": 4}],
            ["note", ("D", '4'),  {"dot": 5}],
            ["note", ("E", '4'),  {"dot": 6}],
            ["note", ("F", '4'),  {"dot": 7}],
            ["note", ("HG", '4'), {"dot": 8}],
            ["note", ("HA", '4'), {"dot": 9}]
        ]
        self._test_helper(test_string, expected)

    def test_gracenotes(self):
        test_string = "lgg lag bg cg dg eg fg gg ag tg"
        expected = [
            ["grace", ("LG",), {}],
            ["grace", ("LA",), {}],
            ["grace", ("B",), {}],
            ["grace", ("C",), {}],
            ["grace", ("D",), {}],
            ["grace", ("E",), {}],
            ["grace", ("F",), {}],
            ["grace", ("HG",), {}],
            ["grace", ("HA",), {}],
            ["grace", ("HA",), {}]
        ]

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
    
    def test_rest(self):
        test_string = "REST_4 REST_8 REST_16"
        expected = [
            ["rest", ('4',), {}],
            ["rest", ('8',), {}],
            ["rest", ('16',), {}]
        ]
        self._test_helper(test_string, expected)

    def test_gracestrike(self):
        test_string = "lgstla lastb bstc cstd dste estf fsthg gsta tstla"
        expected = [
            ["gracestrike", ("LG","LA"), {}],
            ["gracestrike", ("LA","B"), {}],
            ["gracestrike", ("B","C"), {}],
            ["gracestrike", ("C","D"), {}],
            ["gracestrike", ("D","E"), {}],
            ["gracestrike", ("E","F"), {}],
            ["gracestrike", ("F","HG"), {}],
            ["gracestrike", ("HG","HA"), {}],
            ["gracestrike", ("HA","LA"), {}]
        ]
        self._test_helper(test_string, expected)

    def test_triplestrike(self):
        test_string = "st3lg st3la st3b st3c st3d st3e st3f st3hg st3ha"
        expected = [
            ["triplestrike", ("LG",), {}],
            ["triplestrike", ("LA",), {}],
            ["triplestrike", ("B",), {}],
            ["triplestrike", ("C",), {}],
            ["triplestrike", ("D",), {}],
            ["triplestrike", ("E",), {}],
            ["triplestrike", ("F",), {}],
            ["triplestrike", ("HG",), {}],
            ["triplestrike", ("HA",), {}]
        ]
        self._test_helper(test_string, expected)

    def test_doublegrace(self):
        test_string = "lgla lab bc cd ef fhg gla tlg thg"
        expected = [
            ["doublegrace", ("LG","LA"), {}],
            ["doublegrace", ("LA","B"), {}],
            ["doublegrace", ("B","C"), {}],
            ["doublegrace", ("C","D"), {}],
            ["doublegrace", ("E","F"), {}],
            ["doublegrace", ("F","HG"), {}],
            ["doublegrace", ("HG","LA"), {}],
            ["doublegrace", ("HA","LG"), {}],
            ["doublegrace", ("HA","HG"), {}]
        ]
        self._test_helper(test_string, expected)

    def test_time_notation(self):
        test_string = "4_4 6_8 12_8 C C_ c c_"
        expected = [
            ["time_notation", ('4','4'), {}],
            ["time_notation", ('6','8'), {}],
            ["time_notation", ('12','8'), {}],
            ["time_notation", ('4','4'), {}],
            ["time_notation", ('2','2'), {}],
            ["time_notation", ('4','4'), {}],
            ["time_notation", ('2','2'), {}]
        ]
        self._test_helper(test_string, expected)

    def test_clefc(self):
        test_string = "clefc"
        expected = [
            ["clefc", (), {}]
        ]
        self._test_helper(test_string, expected)

    def test_grip(self):
        test_string = "grp hgrp grpb"
        expected = [
            ["grip", (), {}],
            ["grip", (), {"half": True}],
            ["grip", ("B",), {}]
        ]
        self._test_helper(test_string, expected)

    def test_tarluath(self):
        test_string = "tar tarb"
        expected = [
            ["tarluath", (), {}],
            ["dtarluath", (), {}]
        ]
        self._test_helper(test_string, expected)

    def test_darado(self):
        test_string = "bubly darado darodo"
        expected = [
            ["darado", (), {}],
            ["darado", (), {}],
            ["darado", (), {}]
        ]
        self._test_helper(test_string, expected)

    def test_rodin(self):
        test_string = "rodin"
        expected = [
            ["rodin", (), {}]
        ]
        self._test_helper(test_string, expected)

    def test_triplets(self):
        test_string = ""
        expected = [
        ]
        self._test_helper(test_string, expected)

    def test_bars(self):
        test_string = "I!'' ''!I ! !t I! !I ''!It !!t"
        expected = [
            ["repeatstart", (), {}],
            ["repeatend", (), {}],
            ["barend", (), {}],
            ["lineend", (), {}],
            ["partstart", (), {}],
            ["partend", (), {}],
            ["partend", (), {}],
            ["partend", (), {}]
        ]
        self._test_helper(test_string, expected)

    def test_triplets(self):
        test_string = "^2s LG_8 LA_8 ^2e ^3s C_8 D_8 E_8 ^3e gg LA_8 B_8 C_8 ^3lg"
        expected = [
            ["tuplet", (2,), {"state": "start"}],
            ["note", ("LG",8), {"tuplet": 2}],
            ["note", ("LA",8), {"tuplet": 2}],
            ["tuplet", (2,), {"state": "end"}],
            ["tuplet", (3,), {"state": "start"}],
            ["note", ("C",8), {"tuplet": 3}],
            ["note", ("D",8), {"tuplet": 3}],
            ["note", ("E",8), {"tuplet": 3}],
            ["tuplet", (3,), {"state": "end"}],
            ["grace", ("G",), {}],
            ["tuplet", (3,), {"state": "start"}],
            ["note", ("LA",8), {"tuplet": 3}],
            ["note", ("B",8), {"tuplet": 3}],
            ["note", ("C",8), {"tuplet": 3}],
            ["tuplet", (3,), {"state": "end"}]
        ]
        self._test_helper(test_string, expected)

    def test_(self):
        test_string = ""
        expected = [
        ]
        self._test_helper(test_string, expected)

unittest.main()
