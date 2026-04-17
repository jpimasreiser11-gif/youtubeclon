import unittest

from backend.database import get_channel, init_db
from backend.pipeline.metadata_writer import generate_metadata
from backend.pipeline.script_writer import generate_script


class PipelineSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.channel = get_channel("impacto-mundial")

    def test_script_generation_shape(self):
        result = generate_script("Prueba de sistema", self.channel)
        self.assertTrue(result.get("title"))
        self.assertGreater(len(result.get("script", "")), 200)
        self.assertIn("broll_markers", result)

    def test_metadata_generation_shape(self):
        metadata = generate_metadata(
            "Prueba de metadata",
            "## HOOK\nTexto\n## CONTENT\nTexto largo de prueba para metadata.",
            self.channel,
        )
        self.assertTrue(metadata.get("title"))
        self.assertTrue(metadata.get("description"))
        self.assertIn("tags", metadata)

