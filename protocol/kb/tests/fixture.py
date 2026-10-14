"""A small git repository in a temporary directory, for kb.py's tests. Never a real project."""

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import kb  # noqa: E402

ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "kb tests", "GIT_AUTHOR_EMAIL": "kb@tests",
    "GIT_COMMITTER_NAME": "kb tests", "GIT_COMMITTER_EMAIL": "kb@tests",
    "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
}


def pom(artifact, deps=()):
    body = "".join(f"<dependency><artifactId>{d}</artifactId></dependency>" for d in deps)
    return (f'<project xmlns="http://maven.apache.org/POM/4.0.0"><artifactId>{artifact}</artifactId>'
            f"<dependencies>{body}</dependencies></project>\n")


class Repo:
    """A git repository made from a {path: text} map and committed; kb's root points at it."""

    def __init__(self, files):
        self.dir = Path(tempfile.mkdtemp(prefix="kb-test-")).resolve()
        self.git("init", "-q", "-b", "main")
        self.commit(files)
        kb.set_root(self.dir)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.dir, env=ENV, capture_output=True, text=True,
                              check=True).stdout

    def write(self, files):
        for path, text in files.items():
            f = self.dir / path
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text)

    def commit(self, files=None):
        """Writes `files`, commits everything, and returns the new commit's sha."""
        self.write(files or {})
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "change")
        return self.head()

    def head(self):
        return self.git("rev-parse", "HEAD").strip()

    def parts(self, text):
        self.write({"fondue/kb/parts.txt": text})

    def card(self, mid, sha):
        self.write({f"fondue/kb/cards/{mid}.md": f"---\nsummary: x\nverified-at: {sha}\n---\nNothing named.\n"})

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def run(*args):
    """kb.py's command line, in this process (so patched constants hold): its stdout, and its exit message or None."""
    out = io.StringIO()
    argv = sys.argv
    sys.argv = ["kb.py", *args, "--root", str(kb.ROOT)]
    try:
        with contextlib.redirect_stdout(out):
            kb.main()
        code = None
    except SystemExit as e:
        code = e.code
    finally:
        sys.argv = argv
    return out.getvalue(), code
