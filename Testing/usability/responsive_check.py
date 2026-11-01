#!/usr/bin/env python3
"""NFR-04 browser check (Test Plan UT_40, UT_41, UT_42, UT_43).

Opens every screen in a real browser at phone, tablet and desktop widths and
checks the SRS 6.4 rules that unit tests cannot see:

  * no sideways scrolling and nothing sticking out of the screen (>= 360 px)
  * touch targets at least 44 px high, input text at least 16 px
  * the exam flow works: log in, 2 clicks to the attempt page, the timer
    counts down, answers save, Next/Previous/navigator work, reload keeps
    the answer
  * no JavaScript errors on any screen
  * 360 px screenshots (normal and error states) for the test evidence

Setup (Source-Code folder):
    pip install playwright && playwright install chromium firefox
    python manage.py migrate
    python manage.py seed_load_test --students 2 --questions 5
    python manage.py runserver 8000

Run (second terminal):
    python ../Testing/usability/responsive_check.py
    python ../Testing/usability/responsive_check.py --browser firefox

Exit code 0 when every check passes.
"""
import argparse
import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

PASSWORD = "LoadTest123!"
STUDENT = "loadtest1@example.com"
INSTRUCTOR = "loadtest.instructor@example.com"
VIEWPORTS = [("phone-360", 360, 740), ("tablet-768", 768, 1024),
             ("desktop-1280", 1280, 800)]

AUDIT_JS = """
() => {
  const vw = document.documentElement.clientWidth;
  const out = {vw, scrollWidth: document.documentElement.scrollWidth,
               overflowing: [], small: [], smallText: []};
  const label = el => el.tagName.toLowerCase() +
      (el.id ? '#' + el.id : '') +
      (el.className && typeof el.className === 'string'
         ? '.' + el.className.trim().split(/\\s+/).join('.') : '');
  const scrolls = el => {
    for (let e = el.parentElement; e && e !== document.body; e = e.parentElement) {
      const o = getComputedStyle(e).overflowX;
      if (o === 'auto' || o === 'scroll') return true;
    }
    return false;
  };
  const visible = el => {
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    return cs.display !== 'none' && cs.visibility !== 'hidden' &&
           r.width > 1 && r.height > 1 && r.bottom > 0;
  };
  document.querySelectorAll('body *').forEach(el => {
    if (!visible(el)) return;
    const r = el.getBoundingClientRect();
    if (r.right > vw + 1 && !scrolls(el)) {
      out.overflowing.push(label(el) + ' right=' + Math.round(r.right));
    }
  });
  const targets = 'a.btn, button, a.link-btn, .main-nav a, a.brand, ' +
      'input:not([type=hidden]):not([type=radio]):not([type=checkbox]), ' +
      'select, textarea, label.opt, label.checkline';
  document.querySelectorAll(targets).forEach(el => {
    if (!visible(el)) return;
    const h = el.getBoundingClientRect().height;
    if (h < 43.5) out.small.push(label(el) + ' h=' + Math.round(h));
  });
  // The 16 px rule is about fields the user types or picks text in (mobile
  // browsers zoom into smaller ones). Checkboxes and radio buttons hold no
  // text, so they are left out; their size is covered by the 44 px target rule.
  const noText = 'input[type=hidden], input[type=checkbox], input[type=radio], ' +
                 'input[type=submit], input[type=button]';
  document.querySelectorAll('input, select, textarea').forEach(el => {
    if (el.matches(noText) || !visible(el)) return;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < 16) out.smallText.push(label(el) + ' ' + fs + 'px');
  });
  return out;
}
"""


class Checker:
    def __init__(self, base, outdir, browser_name):
        self.base = base.rstrip("/")
        self.outdir = outdir
        self.browser_name = browser_name
        self.rows = []          # (check, detail, ok)
        self.js_errors = []

    def record(self, name, ok, detail=""):
        self.rows.append((name, detail, ok))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" +
              (f" - {detail}" if detail else ""))

    def audit(self, page, name, shot=False):
        for vp_name, w, h in VIEWPORTS:
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(150)
            a = page.evaluate(AUDIT_JS)
            sideways = a["scrollWidth"] > a["vw"] + 1
            problems = []
            if sideways:
                problems.append(f"page scrolls sideways ({a['scrollWidth']} > {a['vw']})")
            if a["overflowing"]:
                problems.append("sticks out: " + "; ".join(a["overflowing"][:3]))
            if a["small"]:
                problems.append("targets under 44px: " + "; ".join(a["small"][:3]))
            if a["smallText"]:
                problems.append("input text under 16px: " + "; ".join(a["smallText"][:3]))
            self.record(f"{name} @ {vp_name}", not problems, " | ".join(problems))
            if shot and vp_name == "phone-360":
                slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
                page.screenshot(path=str(self.outdir / f"{slug}.png"),
                                full_page=True)
        page.set_viewport_size({"width": 360, "height": 740})

    def goto(self, page, path):
        resp = page.goto(self.base + path)
        assert resp and resp.status == 200, f"{path} -> {resp and resp.status}"

    def login(self, page, email, password=PASSWORD):
        self.goto(page, "/login/")
        page.fill("#id_username", email)
        page.fill("#id_password", password)
        page.click("main form button[type=submit]")
        page.wait_for_load_state()

    def submit_form(self, page, server_side=False):
        """Click the form's own submit button, never the header's Logout.

        server_side=True switches off the browser's required-field check so
        an empty form reaches the server and its error messages are shown.
        """
        if server_side:
            page.evaluate("document.querySelectorAll('main form')"
                          ".forEach(f => { f.noValidate = true; })")
        page.click("main form button[type=submit]")
        page.wait_for_load_state()

    def logout(self, page):
        page.click("header button:has-text('Logout')")
        page.wait_for_load_state()

    # ------------------------------------------------------------------

    def run(self):
        with sync_playwright() as p:
            browser = getattr(p, self.browser_name).launch()
            print(f"Browser: {self.browser_name} {browser.version}\n")
            ctx = browser.new_context(viewport={"width": 360, "height": 740})
            page = ctx.new_page()
            page.on("pageerror", lambda e: self.js_errors.append(str(e)))
            page.on("console", lambda m: m.type == "error" and
                    self.js_errors.append(m.text))

            print("Anonymous screens")
            self.goto(page, "/login/"); self.audit(page, "Login", shot=True)
            self.goto(page, "/register/"); self.audit(page, "Register", shot=True)

            print("\nError and confirmation states (UT_43)")
            self.login(page, STUDENT, "wrong-password")
            self.audit(page, "Login error", shot=True)
            first = page.inner_text(".message-error")
            self.login(page, "nobody@example.com", "wrong-password")
            second = page.inner_text(".message-error")
            self.record("Wrong password and unknown email give the same message",
                        first == second and "Invalid email or password" in first,
                        first.strip())
            self.goto(page, "/register/")
            page.fill("#id_username", "u"); page.fill("#id_email", "bad")
            page.fill("#id_password1", "abc"); page.fill("#id_password2", "xyz")
            self.submit_form(page, server_side=True)
            self.audit(page, "Register error", shot=True)
            near = page.locator(".field:has(#id_email) .field-error").count()
            self.record("Register: error sits inside the field it belongs to",
                        near == 1)

            print("\nInstructor screens")
            self.login(page, INSTRUCTOR)
            self.audit(page, "Instructor dashboard", shot=True)
            self.goto(page, "/instructor/exams/"); self.audit(page, "Exam list", shot=True)
            self.goto(page, "/instructor/exams/create/")
            self.audit(page, "Exam form", shot=True)
            self.submit_form(page, server_side=True)
            self.audit(page, "Exam form error", shot=True)
            self.record("Exam form: stays on the form after an empty submit",
                        page.url.endswith("/instructor/exams/create/"), page.url)
            self.record("Exam form: error sits inside the field it belongs to",
                        page.locator(".field:has(#id_title) .field-error").count() == 1)
            self.goto(page, "/questions/"); self.audit(page, "Question list", shot=True)
            self.goto(page, "/questions/create/")
            self.audit(page, "Question form", shot=True)
            self.submit_form(page, server_side=True)
            self.audit(page, "Question form error", shot=True)
            self.record("Question form: error sits inside the field it belongs to",
                        page.locator(".field:has(#id_question_text) .field-error").count() == 1)
            self.goto(page, "/questions/")
            edit = page.locator("a:has-text('Delete')").first.get_attribute("href")
            self.goto(page, edit); self.audit(page, "Question delete", shot=True)
            self.goto(page, "/instructor/exams/")
            del_link = page.locator("a:has-text('Delete')")
            if del_link.count():
                self.goto(page, del_link.first.get_attribute("href"))
                self.audit(page, "Exam delete", shot=True)
            self.logout(page)

            print("\nStudent screens and exam flow")
            self.login(page, STUDENT)
            self.audit(page, "Student dashboard", shot=True)
            self.goto(page, "/student/exams/"); self.audit(page, "Upcoming exams", shot=True)
            page.go_back(); page.wait_for_load_state()

            clicks = 0
            page.locator("a:has-text('Start exam')").first.click()   # click 1
            clicks += 1
            page.wait_for_load_state()
            self.audit(page, "Exam instructions", shot=True)
            page.click("button:has-text('Start exam')")               # click 2
            clicks += 1
            page.wait_for_url(re.compile(r"/attempt/\d+/"))
            self.record("Student reaches the attempt page within 3 clicks "
                        "of logging in (UT_42)", clicks <= 3, f"{clicks} clicks")

            self.audit(page, "Exam attempt", shot=True)
            t1 = page.inner_text("#timer")
            page.wait_for_timeout(2200)
            t2 = page.inner_text("#timer")
            self.record("Countdown timer runs", t1 != t2 and t1 != "--:--",
                        f"{t1} -> {t2}")
            page.locator(".question.active input[type=radio]").first.click()
            page.wait_for_selector("#save-status:has-text('Saved')")
            self.record("Selecting an answer saves it",
                        page.locator(".nav-btn.answered").count() == 1)
            page.click("#next-btn")
            q2 = page.locator(".question.active h3").inner_text()
            page.click("#prev-btn")
            q1 = page.locator(".question.active h3").inner_text()
            self.record("Next and Previous change the question",
                        "Question 2" in q2 and "Question 1" in q1, f"{q2} / {q1}")
            page.locator(".nav-btn").nth(3).click()
            self.record("Navigator jumps to a question",
                        "Question 4" in page.locator(".question.active h3").inner_text())
            page.reload(); page.wait_for_load_state()
            self.record("Answer is kept after reload",
                        page.locator("input[type=radio]:checked").count() == 1)
            self.record("Header keeps user name and Logout during the exam",
                        page.locator("header .user-name").count() == 1 and
                        page.locator("header button:has-text('Logout')").count() == 1)

            print("\nSubmit, results and reports (FR-6, FR-7 screens)")
            page.click("#submit-btn")
            page.wait_for_url(re.compile(r"/attempt/\d+/submit/"))
            self.audit(page, "Submit confirmation", shot=True)
            self.record("Submit asks for confirmation and shows unanswered count",
                        "unanswered" in page.inner_text("main"),
                        page.inner_text("main h1"))
            page.click("button:has-text('Yes, submit my exam')")
            page.wait_for_url(re.compile(r"/results/\d+/"))
            self.audit(page, "Result", shot=True)
            self.record("Result page opens right after submission with a "
                        "confirmation message",
                        "Exam submitted successfully." in
                        page.inner_text(".messages"))
            self.goto(page, "/student/history/")
            self.audit(page, "Exam history", shot=True)
            page.locator("a:has-text('Review Answers')").first.click()
            page.wait_for_load_state()
            self.audit(page, "Answer review", shot=True)
            self.logout(page)
            self.login(page, INSTRUCTOR)
            page.locator("a:has-text('View report')").first.click()
            page.wait_for_load_state()
            self.audit(page, "Exam report", shot=True)
            self.record("Exam report lists the submitted attempt",
                        page.locator("tbody tr").count() >= 1)

            self.record("No JavaScript errors on any screen",
                        not self.js_errors, "; ".join(self.js_errors[:3]))
            browser.close()

        failed = [r for r in self.rows if not r[2]]
        print(f"\n{len(self.rows) - len(failed)} of {len(self.rows)} checks passed")
        (self.outdir / "results.json").write_text(json.dumps(
            [{"check": c, "detail": d, "ok": ok} for c, d, ok in self.rows],
            indent=2))
        return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--browser", default="chromium",
                    choices=["chromium", "firefox", "webkit"])
    ap.add_argument("--out", default="usability-output")
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    return Checker(args.base, out, args.browser).run()


if __name__ == "__main__":
    sys.exit(main())
