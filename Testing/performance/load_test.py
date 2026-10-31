#!/usr/bin/env python3
"""NFR-01 load test: N students take the same exam at the same time.

Standard library only, so it runs anywhere Python 3.11+ runs.

    cd Source-Code
    python manage.py migrate
    python manage.py seed_load_test --students 10 --questions 50
    python manage.py runserver 8000          # in a second terminal
    python ../Testing/performance/load_test.py --students 10
    python ../Testing/performance/load_test.py --students 10 --login-stagger 1

Every student logs in, opens the dashboard and the instructions page, starts
the exam, opens the attempt page, answers every question and (when the submit
endpoint exists) submits and opens the result page. All students start each
step together (a barrier), which is the worst case for "10 students at the
same time". --login-stagger spreads the logins out the way real students
arrive; the default (0) logs everyone in at the same instant.

SRS NFR-1 limits checked:
  * normal pages load within 3 seconds
  * evaluation finishes and the result page opens within 2 seconds of
    submission for exams of up to 50 questions
  * at least 10 students can take an exam at the same time
Exit code is 0 when every limit is met, 1 otherwise.
"""
import argparse
import http.cookiejar
import re
import statistics
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

PASSWORD = "LoadTest123!"
PAGE_LIMIT = 3.0
EVAL_LIMIT = 2.0


class Student:
    def __init__(self, base, number, barrier, login_delay=0.0, burst=True):
        self.login_delay = login_delay
        self.burst = burst  # same for every student, so barrier counts match
        self.base = base.rstrip("/")
        self.email = f"loadtest{number}@example.com"
        self.barrier = barrier
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )
        self.timings = []  # (label, seconds, kind)
        self.errors = []

    def csrf(self):
        for cookie in self.jar:
            if cookie.name == "csrftoken":
                return cookie.value
        return ""

    def request(self, label, path, data=None, kind="page", sync=True):
        if sync:
            self.barrier.wait(timeout=180)
        url = self.base + path
        body = None
        if data is not None:
            data = dict(data, csrfmiddlewaretoken=self.csrf())
            body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=body)
        if body is not None:
            req.add_header("Referer", url)
        started = time.perf_counter()
        try:
            with self.opener.open(req, timeout=60) as resp:
                html = resp.read().decode("utf-8", "replace")
                final_url = resp.geturl()
                status = resp.status
        except urllib.error.HTTPError as err:
            status, html, final_url = err.code, "", url
        elapsed = time.perf_counter() - started
        self.timings.append((label, elapsed, kind))
        return status, html, final_url

    def run(self, submit):
        try:
            self._run(submit)
        except Exception as exc:  # report, don't crash the other threads
            self.errors.append(f"{self.email}: {exc!r}")
            try:
                self.barrier.abort()
            except Exception:
                pass

    def _run(self, submit):
        # Burst mode (delay 0): every student logs in at the same instant.
        # Otherwise each student arrives login_delay seconds after the last.
        time.sleep(self.login_delay)
        self.request("login page", "/login/", sync=False)
        self.request(
            "login", "/login/",
            {"username": self.email, "password": PASSWORD},
            kind="auth", sync=self.burst,
        )
        _, html, _ = self.request("dashboard", "/student/dashboard/")
        match = re.search(r"/exam/(\d+)/instructions/", html)
        if not match:
            raise RuntimeError("no open exam on the dashboard (seed first?)")
        exam_id = match.group(1)
        self.request("instructions", f"/exam/{exam_id}/instructions/")
        _, _, url = self.request(
            "start exam", f"/exam/{exam_id}/start/", {}, kind="action"
        )
        attempt_id = re.search(r"/attempt/(\d+)/", url)
        if not attempt_id:
            raise RuntimeError(f"start did not open an attempt: {url}")
        attempt_id = attempt_id.group(1)
        _, html, _ = self.request("attempt page", f"/attempt/{attempt_id}/")
        question_ids = re.findall(r'data-id="(\d+)"', html)
        if not question_ids:
            raise RuntimeError("attempt page has no questions")
        for qid in question_ids:
            option = re.search(
                rf'name="q{qid}" value="(\d+)"', html
            )
            self.request(
                "save answer",
                f"/attempt/{attempt_id}/answer/",
                {"question": qid, "option": option.group(1) if option else ""},
                kind="action",
                sync=False,
            )
        if submit:
            status, _, final = self.request(
                "submit + result page",
                f"/attempt/{attempt_id}/submit/",
                {},
                kind="evaluation",
            )
            if "/results/" not in final:
                raise RuntimeError(f"submit did not reach results: {final}")


def endpoint_exists(base, path):
    """True when the path is routed (any answer except 404)."""
    try:
        urllib.request.urlopen(base.rstrip("/") + path, timeout=10)
    except urllib.error.HTTPError as err:
        return err.code != 404
    except urllib.error.URLError:
        return True
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--students", type=int, default=10)
    parser.add_argument(
        "--login-stagger", type=float, default=0.0, metavar="SECONDS",
        help="seconds between students logging in (0 = all at once)",
    )
    args = parser.parse_args()

    submit = endpoint_exists(args.base, "/attempt/1/submit/")
    barrier = threading.Barrier(args.students)
    students = [
        Student(args.base, n, barrier, (n - 1) * args.login_stagger,
                burst=(args.login_stagger == 0))
        for n in range(1, args.students + 1)
    ]
    threads = [threading.Thread(target=s.run, args=(submit,)) for s in students]
    started = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    total = time.perf_counter() - started

    errors = [e for s in students for e in s.errors]
    by_label = {}
    for s in students:
        for label, secs, kind in s.timings:
            by_label.setdefault((label, kind), []).append(secs)

    print(f"\n{args.students} concurrent students, total {total:.1f}s\n")
    print(f"{'step':<24}{'n':>5}{'avg':>9}{'p95':>9}{'max':>9}")
    worst_page = worst_eval = worst_login = 0.0
    for (label, kind), values in by_label.items():
        values.sort()
        p95 = values[max(0, int(len(values) * 0.95) - 1)]
        print(
            f"{label:<24}{len(values):>5}{statistics.mean(values):>9.3f}"
            f"{p95:>9.3f}{max(values):>9.3f}"
        )
        if kind == "page":
            worst_page = max(worst_page, max(values))
        if kind == "auth":
            worst_login = max(worst_login, max(values))
        if kind == "evaluation":
            worst_eval = max(worst_eval, max(values))

    print()
    ok = True
    if errors:
        ok = False
        print("ERRORS:")
        for e in errors[:10]:
            print("  ", e)
    print(f"slowest page load : {worst_page:.3f}s (limit {PAGE_LIMIT}s)",
          "OK" if worst_page <= PAGE_LIMIT else "FAIL")
    ok &= worst_page <= PAGE_LIMIT
    print(f"slowest login     : {worst_login:.3f}s (limit {PAGE_LIMIT}s)",
          "OK" if worst_login <= PAGE_LIMIT else "FAIL",
          "- password hashing is CPU-bound by design (NFR-3)"
          if worst_login > PAGE_LIMIT else "")
    ok &= worst_login <= PAGE_LIMIT
    if submit:
        print(f"slowest evaluation: {worst_eval:.3f}s (limit {EVAL_LIMIT}s)",
              "OK" if worst_eval <= EVAL_LIMIT else "FAIL")
        ok &= worst_eval <= EVAL_LIMIT
    else:
        print("evaluation        : SKIPPED (no submit endpoint; FR-6 not "
              "merged into this branch)")
    print(f"{args.students} concurrent students without errors:",
          "OK" if not errors else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
