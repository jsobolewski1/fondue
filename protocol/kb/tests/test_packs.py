"""A directory module's pack: its build and manifest files, and the possible references in other modules."""

import unittest

from fixture import Repo, kb, pom

REFS = "## Possible references in other modules (lines that hold a name only this module declares; " \
       "not evidence of a dependency)\n"

MODULES = {
    "a/registry.py": "def register_handler(name):\n    pass\n\n\ndef lookup_entry(key):\n    pass\n\n\n"
                     "def shared_name_x():\n    pass\n",
    "b/app.py": 'def main():\n    register_handler("x")\n    shared_name_x()\n',
    "b/many.py": 'def setup():\n    register_handler(1)\n    register_handler(2)\n    register_handler(3)\n'
                 '    register_handler(4)\n    load("registry.py")\n',
    "c/notes.sh": "shared_name_x() {\n    true\n}\n\nrun_it() {\n    python3 a/registry.py\n}\n",
    "svc/pom.xml": pom("svc"),
    "svc/src/main/java/app/S.java": 'class S {\n    void go() {\n        run("registry.py");\n'
                                    '        register_handler();\n    }\n}\n',
}


def section(text, title):
    start = text.index(title) + len(title)
    end = text.find("\n## ", start)
    return text[start:] if end < 0 else text[start:end + 1]


class Packs(unittest.TestCase):
    def repo(self, files):
        r = Repo(files)
        self.addCleanup(r.cleanup)
        mods = kb.modules()
        return {mid: kb.pack(m, mods, {}) for mid, m in mods.items()}

    def test_directory_module_wiring(self):
        packs = self.repo({"web/app.ts": "export const a = 1\n",
                           "web/package.json": '{\n  "name": "web",\n\n  "dependencies": {"vue": "3"}\n}\n'})
        self.assertIn('## Wiring\n### package.json\n{\n  "name": "web",\n  "dependencies": {"vue": "3"}\n}\n',
                      packs["web"])

    def test_build_module_wiring_is_unchanged(self):
        packs = self.repo({"pom.xml": pom("app"), "src/main/java/app/A.java": "package app;\nclass A {}\n",
                           "src/main/resources/META-INF/services/app.Plugin": "# comment\napp.Impl\n",
                           "src/main/resources/package.json": "{}\n"})
        self.assertTrue(packs["app"].endswith("## Wiring\n### src/main/resources/META-INF/services/app.Plugin\n"
                                              "app.Impl\n"), packs["app"])

    def test_possible_references(self):
        packs = self.repo(MODULES)
        self.assertEqual(section(packs["a"], REFS), "\n".join([
            '- b/app.py:2: register_handler("x")',
            "- c/notes.sh:6: python3 a/registry.py",
            '- svc/src/main/java/app/S.java:3: run("registry.py");',
            "- b/many.py:2: register_handler(1)",
            "- b/many.py:3: register_handler(2)",
            '- b/many.py:6: load("registry.py")',
        ]) + "\n")
        self.assertIn("depends on (project): -\ndepends on (external): -\ndepended on by: -\n", packs["a"])

    def test_names_another_directory_module_has_are_not_used(self):
        packs = self.repo(MODULES)
        self.assertNotIn("shared_name_x()", section(packs["a"], REFS))
        self.assertNotIn("register_handler();", section(packs["a"], REFS))

    def test_build_module_pack_is_the_same_without_the_directory_module(self):
        with_a = self.repo(MODULES)["svc"]
        without = self.repo({p: t for p, t in MODULES.items() if not p.startswith("a/")})["svc"]
        self.assertEqual(with_a, without)
        self.assertNotIn("Possible references", with_a)


if __name__ == "__main__":
    unittest.main()
