"""The reader that knows no language: each family keeps its declarations and drops its bodies."""

import unittest

from fixture import Repo, kb, pom
from test_modules import JAVA

C = r'''/*
 * Copyright (c) 2026 Someone. Licensed under the MIT licence.
 */

#include <stdio.h>

#define MAX_OF(a, b) ((a) > (b) ? (a) : (b))

typedef struct {
    int id;
    char *name;
} item_t;

static const char *PREFIX = "{\"e\":[";

static int item_print(item_t *item,
                      FILE *out,
                      int flags)
{
    if (flags) {
        fprintf(out, "%d\n", item->id);
    }
    return 0;
}
'''

PYTHON = '''import os


class Store:
    """Keeps things."""

    def get(self, key):
        """Returns the value."""
        return self.data[key]

    def put(self, key, value):
        self.data[key] = value


def helper(x):
    return x * 2
'''

VUE = '''<template>
  <div>{{ count }}</div>
</template>

<script>
export default {
  data() {
    return { count: 0 };
  },
  methods: {
    increment(step) {
      this.count += step;
    },
  },
};
</script>
'''

SHELL = '''#!/bin/sh
set -e

greet() {
    name="$1"
    echo "hello $name"
}

greet world
echo done
'''

TYPESCRIPT = r'''export interface Options {
  strict: boolean
  name?: string
}

const SCHEME = /^https?:\/\//

export function build(
  options: Options,
  extra: string[],
): string {
  const parts = [options.name, ...extra]
  return parts.join('/')
}
'''

KOTLIN = '''class B {
    fun go(x: Int): Int {
        return x + 1
    }
}
'''


class Reader(unittest.TestCase):
    def test_c(self):
        self.assertEqual(kb.generic_skeleton(C), "\n".join([
            "#include <stdio.h>",
            "#define MAX_OF(a, b) ((a) > (b) ? (a) : (b))",
            "typedef struct {",
            "    int id;",
            "    char *name;",
            "} item_t;",
            'static const char *PREFIX = "{\\"e\\":[";',
            "static int item_print(item_t *item,",
            "                      FILE *out,",
            "                      int flags)",
            "{",
            "}",
        ]))

    def test_python(self):
        self.assertEqual(kb.generic_skeleton(PYTHON), "\n".join([
            "import os",
            "class Store:",
            '    """Keeps things."""',
            "    def get(self, key):",
            "    def put(self, key, value):",
            "def helper(x):",
        ]))

    def test_vue_component_as_an_object(self):
        self.assertEqual(kb.generic_skeleton(VUE), "\n".join([
            "<template>",
            "  <div>{{ count }}</div>",
            "</template>",
            "<script>",
            "export default {",
            "  data() {",
            "  },",
            "  methods: {",
            "    increment(step) {",
            "    },",
            "  },",
            "};",
            "</script>",
        ]))

    def test_shell(self):
        self.assertEqual(kb.generic_skeleton(SHELL), "\n".join([
            "#!/bin/sh",
            "set -e",
            "greet() {",
            "}",
            "greet world",
            "echo done",
        ]))

    def test_typescript(self):
        self.assertEqual(kb.generic_skeleton(TYPESCRIPT), "\n".join([
            "export interface Options {",
            "  strict: boolean",
            "  name?: string",
            "}",
            r"const SCHEME = /^https?:\/\//",
            "export function build(",
            "  options: Options,",
            "  extra: string[],",
            "): string {",
            "}",
        ]))

    def test_long_line_is_cut_and_closed(self):
        line = "result = compute(alpha, [" + ", ".join(f"item{i}" for i in range(60))
        out = kb.generic_skeleton(line + "\n])\nnext_thing = 1\n").splitlines()
        self.assertEqual(out, [line[:220] + "…])", "])", "next_thing = 1"])

    def test_comment_kept_above_a_shown_declaration_only(self):
        src = "/**\n * Makes a thing.\n * More.\n */\nint make(void)\n{\n    /* inside */\n    return 1;\n}\n"
        self.assertEqual(kb.generic_skeleton(src), "// Makes a thing.\nint make(void)\n{\n}")


class MixedBuildModule(unittest.TestCase):
    def test_java_by_its_reader_and_kotlin_by_the_generic_one(self):
        r = Repo({"pom.xml": pom("app"), "src/main/java/app/A.java": JAVA, "src/main/kotlin/B.kt": KOTLIN})
        self.addCleanup(r.cleanup)
        mods = kb.modules()
        text = kb.pack(mods["app"], mods, {})
        self.assertIn("### src/main/java/app/A.java\n" + kb.java_skeleton(JAVA) + "\n\n"
                      "### src/main/kotlin/B.kt\nclass B {\n    fun go(x: Int): Int {\n    }\n}\n", text)
        self.assertNotIn("names only", text)


if __name__ == "__main__":
    unittest.main()
