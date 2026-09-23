from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "docs" / "index.html"


def all_js():
    paths = [ROOT / "docs" / "app.js"] + sorted((ROOT / "docs" / "js").glob("*.js"))
    return "\n".join(path.read_text(encoding="utf-8") for path in paths if path.exists())


def all_css():
    paths = [ROOT / "docs" / "styles.css"] + sorted((ROOT / "docs" / "styles").glob("*.css"))
    return "\n".join(path.read_text(encoding="utf-8") for path in paths if path.exists())


class StaticUITests(unittest.TestCase):
    def test_human_write_actions_link_to_github(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn("/issues/new?template=idea.yml", html)
        self.assertNotIn("/issues/new/choose", html)
        self.assertIn("New note", html)
        self.assertIn("What's on your mind?", html)

    def test_review_replaces_cards_and_uses_modules(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn('data-view="notes"', html)
        self.assertIn('data-view="review"', html)
        self.assertIn('data-view="board"', html)
        self.assertIn('data-view="calendar"', html)
        self.assertNotIn('data-view="cards"', html)
        self.assertIn('type="module"', html)
        self.assertIn('./js/app.js', html)

    def test_default_language_is_notes_not_journey_or_marketing(self):
        html = HTML.read_text(encoding="utf-8")
        js = all_js()
        combined = html + "\n" + js
        self.assertIn('view:"notes"', js.replace(" ", ""))
        self.assertNotIn("Capture now. Organize later.", combined)
        self.assertNotIn("Capture an idea", combined)
        self.assertNotIn("Latest", combined)

    def test_review_source_has_three_sections(self):
        path = ROOT / "docs" / "js" / "review.js"
        self.assertTrue(path.exists())
        review = path.read_text(encoding="utf-8")
        for label in ("Needs review", "Worth revisiting", "Rediscover"):
            self.assertIn(label, review)

    def test_frontend_uses_new_generated_data_paths(self):
        path = ROOT / "docs" / "js" / "data.js"
        self.assertTrue(path.exists())
        data = path.read_text(encoding="utf-8")
        self.assertIn("./data/ideas.json", data)
        self.assertIn("./data/ai-insights.json", data)

    def test_client_contains_no_write_api_or_credentials(self):
        text = (HTML.read_text(encoding="utf-8") + "\n" + all_js()).lower()
        forbidden = ("authorization: bearer", "github_token", "api.github.com/repos/", 'method:"post"', 'method:"patch"')
        for token in forbidden:
            self.assertNotIn(token, text)

    def test_metadata_remains_quiet_in_notes(self):
        js = all_js()
        self.assertNotIn("latest-badge", js)
        self.assertIn("note-meta", js)
        self.assertIn("View on GitHub", js)

    def test_css_has_no_heavy_effects(self):
        css = all_css().lower()
        self.assertNotIn("backdrop-filter", css)
        self.assertNotIn("linear-gradient", css)
        self.assertNotIn("radial-gradient", css)
        self.assertNotIn("@keyframes", css)


if __name__ == "__main__":
    unittest.main()
