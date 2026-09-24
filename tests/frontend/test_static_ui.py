from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
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
        normal_css = "\n".join(
            path.read_text(encoding="utf-8").lower()
            for path in (ROOT / "docs" / "styles").glob("*.css")
            if path.name not in {"ticker.css", "boot.css"}
        )
        self.assertNotIn("backdrop-filter", normal_css)
        self.assertNotIn("linear-gradient", normal_css)
        self.assertNotIn("radial-gradient", normal_css)
        self.assertNotIn("@keyframes", normal_css)

    def test_ticker_markup_has_no_literal_backslash_n(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertNotIn(r'</aside>\n  <template', html)

    def test_app_wires_ticker_renderer(self):
        app = (ROOT / "docs" / "js" / "app.js").read_text(encoding="utf-8")
        self.assertIn('from "./ticker.js"', app)
        self.assertIn("buildTickerItems", app)
        self.assertIn("renderTicker", app)

    def test_ticker_contract(self):
        html = HTML.read_text(encoding="utf-8")
        ticker_path = ROOT / "docs" / "js" / "ticker.js"
        css_path = ROOT / "docs" / "styles" / "ticker.css"
        self.assertIn('id="ticker"', html)
        self.assertTrue(ticker_path.exists())
        ticker = ticker_path.read_text(encoding="utf-8")
        css = css_path.read_text(encoding="utf-8")
        self.assertIn("buildTickerItems", ticker)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn(":hover", css)
        self.assertIn(":focus-within", css)
        self.assertIn("@media(max-width:620px)", css)
        self.assertIn("@keyframes ticker-scroll", css)
        compact = css.replace(" ", "").replace("\n", "")
        self.assertIn("@media(prefers-reduced-motion:reduce){.ticker-track{animation:none;transform:none}", compact)
        self.assertIn("@media(max-width:620px){.ticker{position:relative;", compact)

    def test_desktop_uses_quiet_sidebar_instead_of_top_tabs(self):
        html = HTML.read_text(encoding="utf-8")
        css = all_css().replace(" ", "").replace("\n", "")
        self.assertIn('class="sidebar"', html)
        self.assertIn('class="sidebar-nav"', html)
        self.assertIn('class="sidebar-new-note"', html)
        self.assertNotIn('class="tabs"', html)
        self.assertIn('.sidebar{position:fixed;', css)
        self.assertIn('width:180px', css)

    def test_mobile_uses_fixed_bottom_view_navigation(self):
        html = HTML.read_text(encoding="utf-8")
        css = all_css().replace(" ", "").replace("\n", "")
        self.assertIn('class="mobile-nav"', html)
        for view in ("notes", "review", "board", "calendar"):
            self.assertGreaterEqual(html.count(f'data-view="{view}"'), 2)
        self.assertIn('@media(max-width:620px){', css)
        self.assertIn('.mobile-nav{display:grid;position:fixed;', css)
        self.assertIn('padding-bottom:58px', css)

    def test_app_wires_sidebar_and_mobile_view_controls(self):
        app = (ROOT / "docs" / "js" / "app.js").read_text(encoding="utf-8")
        compact = app.replace(" ", "").replace("\n", "")
        self.assertIn('$('.replace(" ", ""), compact)
        self.assertIn('".view-link"', app)
        self.assertIn('".theme-toggle"', app)
        self.assertIn('aria-current', app)

    def test_desktop_sidebar_supports_chatgpt_style_collapsed_rail(self):
        html = HTML.read_text(encoding="utf-8")
        css = all_css().replace(" ", "").replace("\n", "")
        app = (ROOT / "docs" / "js" / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="sidebar"', html)
        self.assertIn('class="sidebar-brand-slot"', html)
        self.assertIn('class="sidebar-brand-mark"', html)
        self.assertIn('class="sidebar-brand-toggle"', html)
        self.assertIn('id="sidebarToggle"', html)
        self.assertIn('data-tooltip="Review"', html)
        self.assertIn('data-tooltip="Calendar"', html)
        self.assertIn('.sidebar.is-collapsed{width:58px', css)
        self.assertIn('.sidebar-brand-slot:hover.sidebar-brand-toggle', css)
        self.assertIn("brainDumpSidebarCollapsed", app)
        self.assertIn("localStorage", app)

    def test_landing_greeting_is_centered_before_composer_and_time_aware(self):
        html = HTML.read_text(encoding="utf-8")
        css = all_css().replace(" ", "").replace("\n", "")
        app = (ROOT / "docs" / "js" / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="greeting"', html)
        self.assertIn('id="greetingTitle"', html)
        self.assertIn('id="greetingSubtitle"', html)
        self.assertLess(html.index('id="greeting"'), html.index('class="composer"'))
        self.assertIn('.landing-intro{text-align:center;', css)
        self.assertIn('min-height:clamp(360px,62vh,560px)', css)
        self.assertIn("greetingForHour", app)
        for greeting in ("Good morning", "Good afternoon", "Good evening", "Good night"):
            self.assertIn(greeting, app)

    def test_futuristic_boot_intro_runs_once_per_session_and_respects_reduced_motion(self):
        html = HTML.read_text(encoding="utf-8")
        app = (ROOT / "docs" / "js" / "app.js").read_text(encoding="utf-8")
        boot_path = ROOT / "docs" / "styles" / "boot.css"
        self.assertIn('./styles/boot.css', html)
        self.assertIn('id="bootIntro"', html)
        self.assertIn("brainDumpBootSeen", app)
        self.assertIn("sessionStorage", app)
        self.assertTrue(boot_path.exists())
        if boot_path.exists():
            boot = boot_path.read_text(encoding="utf-8")
            self.assertIn("@keyframes boot-flicker", boot)
            self.assertIn("@keyframes ui-power-on", boot)
            self.assertIn("prefers-reduced-motion", boot)

    def test_sidebar_review_and_calendar_use_professional_svg_icons(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn('data-icon="review"', html)
        self.assertIn('data-icon="calendar"', html)
        self.assertGreaterEqual(html.count('class="nav-icon"'), 6)
        self.assertGreaterEqual(html.count("<svg"), 6)


if __name__ == "__main__":
    unittest.main()
