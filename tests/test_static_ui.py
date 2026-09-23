from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "docs" / "index.html"
JS = ROOT / "docs" / "app.js"
CSS = ROOT / "docs" / "styles.css"


class StaticUITests(unittest.TestCase):
    def test_human_write_actions_link_to_github(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn("/issues/new?template=idea.yml", html)
        self.assertNotIn("/issues/new/choose", html)
        self.assertIn("New note", html)
        self.assertIn("What's on your mind?", html)

    def test_default_language_is_notes_not_journey_or_marketing(self):
        html = HTML.read_text(encoding="utf-8")
        js = JS.read_text(encoding="utf-8")
        combined = html + "\n" + js
        self.assertIn('data-view="notes"', html)
        self.assertIn('view:"notes"', js)
        self.assertNotIn("Capture now. Organize later.", combined)
        self.assertNotIn("Capture an idea", combined)
        self.assertNotIn("Latest", combined)

    def test_client_contains_no_write_api_or_credentials(self):
        text = (HTML.read_text(encoding="utf-8") + "\n" + JS.read_text(encoding="utf-8")).lower()
        forbidden = (
            "authorization: bearer",
            "github_token",
            "api.github.com/repos/",
            'method:"post"',
            'method:"patch"',
        )
        for token in forbidden:
            self.assertNotIn(token, text)

    def test_metadata_is_not_rendered_as_uppercase_status_pills_in_notes(self):
        js = JS.read_text(encoding="utf-8")
        self.assertNotIn("latest-badge", js)
        self.assertIn("note-meta", js)
        self.assertIn("View on GitHub", js)

    def test_css_has_no_heavy_effects(self):
        css = CSS.read_text(encoding="utf-8").lower()
        self.assertNotIn("backdrop-filter", css)
        self.assertNotIn("linear-gradient", css)
        self.assertNotIn("radial-gradient", css)
        self.assertNotIn("@keyframes", css)


if __name__ == "__main__":
    unittest.main()
