import unittest
from bpmusictransposer.newmusicparser import MusicParser

class TestPretokenizeParser(unittest.TestCase):
    @classmethod
    def setUp(self):
        self.maxDiff = None
        self.parser = MusicParser.parsers["BagpipeMusicWriter"]

    def _test_helper(self, test_string, exp_result):
        tune = self.parser.get_tune(test_string)
        self.assertEqual(exp_result, tune.notes)

    def test_crunluath(self):
        test_string = "crunl crunlb hcrunlla hcrunllgla"
        expected = [
            ["crunluath", (), {}],
            ["crunluath", ("B"), {}],
            ["crunluath", ("LA"), {"heavy": True}],
            ["crunluath", ("LG", "LA"), {"heavy": True}]
        ]
        self._test_helper(test_string, expected)

    def test_crunluath_p_notation(self):
        test_string = "pc pcb phcla"
        expected = [
            ["crunluath", (), {"pio": True}],
            ["crunluath", ("B"), {"pio": True}],
            ["crunluath", ("LA"), {"pio": True}],
        ]

unittest.main()
