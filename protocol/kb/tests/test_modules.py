"""Modules for every project: sources, parts.txt, directory modules, and the commands that count their changes."""

import unittest
from pathlib import Path
from unittest import mock

from fixture import Repo, kb, pom, run

JAVA = "package app;\n\npublic class A {\n    public void go() {\n        int x = 1;\n    }\n}\n"


class RepoTest(unittest.TestCase):
    def repo(self, files):
        r = Repo(files)
        self.addCleanup(r.cleanup)
        return r

    def ids(self):
        return sorted(kb.modules())

    def changed(self, sha):
        return kb.changed_modules(sha, kb.modules())

    def status_counts(self):
        """`kb.py status`'s changed column, by module."""
        out, _ = run("status")
        rows = [line.split() for line in out.splitlines()[1:-1]]
        return {r[0]: r[1] for r in rows if len(r) >= 2 and r[1].isdigit()}


class Sources(RepoTest):
    def sources(self, files, rules=()):
        self.repo(files)
        mains = set(kb.build_mains(kb.modules()))
        return {str(f) for f in kb.tracked() if kb.is_source(f, mains, list(rules))}

    def test_each_rule(self):
        files = {
            "fondue/kb/tool.py": "x\n",
            "pom.xml": pom("app"),
            "src/main/java/app/A.java": JAVA,
            "src/test/java/app/ATest.java": JAVA,
            "src/test/helper.ts": "x\n",
            ".github/ci.sh": "x\n",
            "keep.py": "x\n",
            "UPPER.PY": "x\n",
            "Dockerfile.edge": "FROM x\n",
            "Makefile": "all:\n",
            "LICENSE": "x\n",
            "notes.md": "x\n",
            "data.json": "{}\n",
        }
        for d in sorted(kb.TEST_DIRS | kb.VENDOR_DIRS):
            files[f"lib/{d}/x.c"] = "x\n"
        for name in ("test_one.py", "one_test.go", "one.test.ts", "one.spec.js", "one_spec.rb", "OneTest.java",
                     "OneTests.java"):
            files[f"lib/{name}"] = "x\n"
        self.assertEqual(self.sources(files), {"keep.py", "UPPER.PY", "Dockerfile.edge", "Makefile"})

    def test_submodule_is_skipped(self):
        r = self.repo({"run.sh": "x\n"})
        r.git("update-index", "--add", "--cacheinfo", f"160000,{r.head()},ext.sh")
        r.git("commit", "-q", "-m", "submodule")
        self.assertIn("ext.sh", r.git("ls-files"))
        self.assertNotIn(Path("ext.sh"), kb.tracked())
        self.assertEqual(kb.modules()["root"].sources, [Path("run.sh")])

    def test_exclude_directory_removes_module(self):
        r = self.repo({"a/x.py": "x\n", "old/y.py": "x\n"})
        self.assertEqual(self.ids(), ["a", "old"])
        r.parts("- old\n")
        self.assertEqual(self.ids(), ["a"])

    def test_exclude_glob_removes_files(self):
        r = self.repo({"a/x.py": "x\n", "a/deep/y.min.js": "x\n", "a/z.min.js": "x\n"})
        r.parts("- *.min.js\n")
        self.assertEqual(kb.modules()["a"].sources, [Path("a/x.py")])

    def test_include_makes_a_source_where_there_was_none(self):
        r = self.repo({"lang/main.foo": "fn main() {}\n", "README.md": "x\n"})
        out, code = run("modules")
        self.assertIn("no source found", code)
        r.parts("# my language\n+ *.foo\n")
        out, code = run("modules")
        self.assertIsNone(code)
        self.assertEqual(self.ids(), ["lang"])
        self.assertEqual(kb.modules()["lang"].sources, [Path("lang/main.foo")])

    def test_include_reaches_where_the_defaults_do_not(self):
        r = self.repo({"a/x.py": "x\n", "a/tests/fix.py": "x\n"})
        r.parts("+ a/tests\n")
        self.assertEqual(kb.modules()["a"].sources, [Path("a/tests/fix.py"), Path("a/x.py")])

    def test_exclude_wins_over_include(self):
        r = self.repo({"a/x.py": "x\n", "a/y.foo": "x\n"})
        r.parts("+ *.foo\n- a/y.foo\n")
        self.assertEqual(kb.modules()["a"].sources, [Path("a/x.py")])

    def test_malformed_line_names_its_line(self):
        r = self.repo({"a/x.py": "x\n"})
        r.parts("# comment\n\n- old\nonly-one-word\n")
        with self.assertRaises(SystemExit) as e:
            kb.modules()
        self.assertIn("parts.txt:4: expected", str(e.exception.code))
        self.assertIn("`- <pattern>`", str(e.exception.code))


class DirectoryModules(RepoTest):
    def big(self):
        """`big/` over the budget: two children above the floor, one under it, and a file of its own."""
        return {"big/top.c": "x" * 10, "big/l1/x.c": "x" * 600, "big/l2/y.c": "x" * 600, "big/s/z.c": "x" * 50,
                "tiny/t.c": "x" * 10}

    def setUp(self):
        for name, value in (("BUDGET", 1000), ("FLOOR", 100)):
            p = mock.patch.object(kb, name, value)
            p.start()
            self.addCleanup(p.stop)

    def test_root_and_first_level_directory(self):
        self.repo({"setup.sh": "x\n", "a/x.py": "x\n"})
        mods = kb.modules()
        self.assertEqual(sorted(mods), ["a", "root"])
        self.assertEqual(mods["root"].path, Path("."))
        self.assertTrue(mods["root"].residual)

    def test_size_split_folds_small_children(self):
        self.repo(self.big())
        mods = kb.modules()
        self.assertEqual(sorted(mods), ["big", "big-l1", "big-l2", "tiny"])
        self.assertTrue(mods["big"].residual)
        self.assertEqual(mods["big"].folded, [Path("big/s")])
        self.assertEqual(mods["big"].sources, [Path("big/s/z.c"), Path("big/top.c")])
        self.assertEqual(mods["tiny"].sources, [Path("tiny/t.c")])
        self.assertFalse(mods["tiny"].residual)

    def test_structural_split_reaches_the_build_module(self):
        self.repo({"tools/run.sh": "x\n", "tools/small/x.sh": "x\n",
                   "tools/svc/pom.xml": pom("svc"), "tools/svc/src/main/java/app/A.java": JAVA,
                   "tools/svc/helper.py": "x\n"})
        mods = kb.modules()
        self.assertEqual(sorted(mods), ["svc", "tools", "tools-small", "tools-svc"])
        self.assertEqual(mods["svc"].kind, "build")
        self.assertEqual(mods["tools-svc"].sources, [Path("tools/svc/helper.py")])
        self.assertTrue(mods["tools-svc"].residual)
        self.assertFalse(mods["tools-small"].residual)

    def test_residual_beside_a_build_module_at_the_root(self):
        r = self.repo({"pom.xml": pom("app"), "src/main/java/app/A.java": JAVA, "Makefile": "all:\n"})
        mods = kb.modules()
        self.assertEqual(sorted(mods), ["app", "root"])
        self.assertEqual(mods["root"].sources, [Path("Makefile")])
        base = r.head()
        r.card("app", base)
        r.card("root", base)
        sha = r.commit({"src/main/java/app/A.java": JAVA + "// one\n"})
        self.assertEqual(self.changed(sha + "~1"), {"app"})
        self.assertEqual(self.status_counts(), {"app": "1", "root": "0"})
        sha = r.commit({"Makefile": "all:\n\techo\n"})
        self.assertEqual(self.changed(sha + "~1"), {"root"})
        self.assertEqual(self.status_counts(), {"app": "1", "root": "1"})
        sha = r.commit({"pom.xml": pom("app") + "\n"})
        self.assertEqual(self.changed(sha + "~1"), {"app"})
        self.assertEqual(self.status_counts(), {"app": "1", "root": "1"})

    def test_source_beside_src_main(self):
        files = {"pom.xml": pom("app", deps=["src"]), "src/main/java/app/A.java": JAVA}
        self.repo(files)
        alone = kb.pack(kb.modules()["app"], kb.modules(), {})
        r = self.repo({**files, "src/frontend/app.ts": "export const a = 1\n"})
        mods = kb.modules()
        self.assertEqual(sorted(mods), ["app", "src"])
        self.assertEqual(mods["src"].sources, [Path("src/frontend/app.ts")])
        self.assertIn(":(exclude)src/main", kb.pathspecs(mods["src"], mods))
        self.assertEqual(kb.pack(mods["app"], mods, {}), alone)
        base = r.head()
        r.card("app", base)
        r.card("src", base)
        sha = r.commit({"src/frontend/app.ts": "export const a = 2\n"})
        self.assertEqual(self.changed(sha + "~1"), {"src"})
        sha = r.commit({"src/main/java/app/A.java": JAVA + "// one\n"})
        self.assertEqual(self.changed(sha + "~1"), {"app"})
        self.assertEqual(self.status_counts(), {"app": "1", "src": "2"})

    def test_changes_count_against_their_owner(self):
        r = self.repo(self.big())
        base = r.head()
        for mid in kb.modules():
            r.card(mid, base)
        sha = r.commit({"big/top.c": "y" * 10})
        self.assertEqual(self.changed(sha + "~1"), {"big"})
        sha = r.commit({"big/s/z.c": "y" * 50})
        self.assertEqual(self.changed(sha + "~1"), {"big"})
        sha = r.commit({"big/l1/x.c": "y" * 600})
        self.assertEqual(self.changed(sha + "~1"), {"big-l1"})
        self.assertEqual(self.changed(base), {"big", "big-l1"})
        self.assertEqual(self.status_counts(), {"big": "4", "big-l1": "2", "big-l2": "0", "tiny": "0"})

    def test_id_clash_gets_dir(self):
        self.repo({"svc/pom.xml": pom("lib"), "svc/src/main/java/app/A.java": JAVA, "lib/x.py": "x\n"})
        mods = kb.modules()
        self.assertEqual(sorted(mods), ["lib", "lib-dir"])
        self.assertEqual(mods["lib"].kind, "build")
        self.assertEqual(mods["lib-dir"].path, Path("lib"))

    def test_part_inside_a_group(self):
        r = self.repo({"a/x.py": "x\n", "a/sub/y.py": "x\n"})
        r.parts("a-sub a/sub\n")
        mods = kb.modules()
        self.assertEqual(sorted(mods), ["a", "a-sub"])
        self.assertEqual(mods["a"].sources, [Path("a/x.py")])
        self.assertEqual((mods["a-sub"].kind, mods["a-sub"].parent), ("dir", "a"))
        sha = r.commit({"a/sub/y.py": "y\n"})
        self.assertEqual(self.changed(sha + "~1"), {"a-sub"})

    def test_part_inside_a_folded_child(self):
        r = self.repo(self.big())
        r.parts("big-s big/s\n")
        mods = kb.modules()
        self.assertIn("big-s", mods)
        self.assertEqual(mods["big-s"].sources, [Path("big/s/z.c")])
        self.assertEqual(mods["big"].sources, [Path("big/top.c")])
        self.assertIn("holds: the files directly in big\n", kb.pack(mods["big"], mods, {}))
        base = r.head()
        r.card("big", base)
        r.card("big-s", base)
        sha = r.commit({"big/s/z.c": "y" * 50})
        self.assertEqual(self.changed(sha + "~1"), {"big-s"})
        self.assertEqual(self.status_counts()["big"], "0")
        self.assertEqual(self.status_counts()["big-s"], "2")

    def test_part_over_more_than_one_module(self):
        r = self.repo({"core/pom.xml": pom("core"), "core/src/main/java/app/A.java": JAVA,
                       "api/pom.xml": pom("api"), "api/src/main/java/app/B.java": JAVA})
        r.parts("core-all core\n")
        with self.assertRaises(SystemExit) as e:
            kb.modules()
        self.assertEqual(e.exception.code, "fondue/kb/parts.txt:1: core is not inside one module")

    def test_part_wider_than_its_module(self):
        r = self.repo({"big/a.c": "x" * 10, "big/l1/x.c": "x" * 600, "big/l2/y.c": "x" * 600})
        r.parts("big-all big\n")
        with self.assertRaises(SystemExit) as e:
            kb.modules()
        self.assertEqual(e.exception.code, "fondue/kb/parts.txt:1: big is not inside one module")

    def test_build_file_in_a_group_counts_against_it(self):
        r = self.repo({"shared/build.gradle.kts": "plugins {}\n", "shared/src/commonMain/kotlin/A.kt": "class A\n"})
        self.assertEqual(sorted(kb.modules()), ["shared"])
        r.card("shared", r.head())
        sha = r.commit({"shared/build.gradle.kts": "plugins { kotlin }\n"})
        self.assertEqual(self.changed(sha + "~1"), {"shared"})
        self.assertEqual(self.status_counts(), {"shared": "2"})

    def test_part_outside_every_module(self):
        r = self.repo({"a/x.py": "x\n", "docs/y.md": "x\n"})
        r.parts("d docs\n")
        with self.assertRaises(SystemExit) as e:
            kb.modules()
        self.assertIn("parts.txt:1: docs is in no module", str(e.exception.code))

    def test_non_ascii_name(self):
        r = self.repo({"a/é.sh": "x\n"})
        mods = kb.modules()
        self.assertEqual(mods["a"].sources, [Path("a/é.sh")])
        r.card("a", r.head())
        sha = r.commit({"a/é.sh": "y\n"})
        self.assertEqual(self.changed(sha + "~1"), {"a"})
        self.assertEqual(self.status_counts(), {"a": "2"})

    def test_root_skill_mentions_match_no_unrelated_line(self):
        self.repo({"setup.sh": "x\n", "a/x.py": "x\n",
                   ".claude/skills/ops/SKILL.md": "---\ndescription: ops\n---\nDeploy with care.\nThe a module.\n"})
        mods, skills = kb.modules(), kb.skills()
        self.assertEqual(kb.skill_mentions(mods["root"], skills, set()), {})
        self.assertEqual(kb.skill_mentions(mods["a"], skills, set()), {"ops": ["The a module."]})


class Commands(RepoTest):
    def test_directory_module_pack(self):
        with mock.patch.object(kb, "BUDGET", 1000), mock.patch.object(kb, "FLOOR", 100):
            self.repo({"big/top.c": "x" * 10, "big/l1/x.c": "x" * 600, "big/l2/y.c": "x" * 600,
                       "big/s/z.c": "x" * 50, "big/s/Q.java": "public class Q {}\n"})
            mods = kb.modules()
            text = kb.pack(mods["big"], mods, {})
        self.assertIn("# Module big\npath: big\nholds: the files directly in big, and big/s/\n"
                      "depends on (project): -\ndepends on (external): -\ndepended on by: -\n", text)
        self.assertIn("### s/Q.java\npublic class Q {\n}", text)
        self.assertIn("### s/z.c\n" + "x" * 50 + "\n\n### top.c\n" + "x" * 10 + "\n", text)
        self.assertNotIn("names only", text)
        self.assertNotIn("## Wiring", text)

    def test_build_module_reads_every_source_under_src_main(self):
        self.repo({"pom.xml": pom("app"), "src/main/java/app/A.java": JAVA, "src/main/kotlin/B.kt": "class B\n",
                   "src/main/js/c.js": "x\n"})
        mods = kb.modules()
        text = kb.pack(mods["app"], mods, {})
        self.assertIn("### src/main/js/c.js\nx\n\n### src/main/kotlin/B.kt\nclass B\n", text)
        self.assertNotIn("names only", text)

    def test_modules_prints_size(self):
        self.repo({"a/x.py": "x" * 2500, "a/y.py": "x" * 600})
        out, _ = run("modules")
        line = out.splitlines()[0].split()
        self.assertEqual(line, ["a", "a", "2", "files", "3k"])
        self.assertEqual(out.splitlines()[-1], "1 modules")

    def test_no_source_exits(self):
        self.repo({"README.md": "x\n", "data.json": "{}\n"})
        out, code = run("modules")
        self.assertEqual(code, "no source found: kb.py found no build-file module and no tracked source file; "
                               "an include line in fondue/kb/parts.txt can name one (protocol/kb.md)")

    def test_estimate_write_since_and_touched(self):
        r = self.repo({"setup.sh": "x\n", "a/x.py": "x\n", "b/y.py": "x\n",
                       ".claude/skills/ops/SKILL.md": "---\ndescription: ops\n---\nThe a module.\n"})
        base = r.head()
        r.card("b", base)
        r.card("root", base)
        sha = r.commit({"a/x.py": "y\n", "b/notes.md": "x\n"})
        out, code = run("estimate", "--since", base)
        self.assertIsNone(code)
        self.assertTrue(out.startswith("2 cards:"), out)
        out, _ = run("touched", base)
        self.assertIn("modules: a, b\n", out)
        self.assertIn("ops (.claude/skills/ops/SKILL.md) - a", out)
        written = []

        def writer(mid, text, model, v):
            written.append((mid, text))
            return "---\nsummary: new\n---\nBody.\n"

        with mock.patch.object(kb, "call_writer", writer):
            out, code = run("write", "--since", base)
        self.assertIsNone(code)
        self.assertEqual(sorted(mid for mid, _ in written), ["a", "b"])
        self.assertIn("# Module a\npath: a\n", dict(written)["a"])
        self.assertIn(f"verified-at: {sha[:7]}", (r.dir / "fondue/kb/cards/a.md").read_text())
        self.assertIn("- **root** [card](cards/root.md)", (r.dir / "fondue/kb/index.md").read_text())


if __name__ == "__main__":
    unittest.main()
