# Enhancing rstcheck-core to Respect conf.py Files

## Problem Statement

rstcheck-core currently doesn't fully respect conf.py files used in Sphinx documentation projects. This leads to false positive errors when checking RST files that use features defined in conf.py, such as:

1. Custom roles (e.g., `:wiki:`)
2. Custom substitutions (e.g., `|build|`)
3. Link targets (e.g., `_build`)
4. Combined substitution and link references (e.g., `|build|_`)

When these elements are defined in a conf.py file but used in RST files, rstcheck-core reports them as errors because it doesn't properly load and process the definitions from conf.py.

## Current Behavior

When running rstcheck on a file that uses elements defined in conf.py, it reports errors like:

```
peru_user_guide/index.rst:43: (INFO/1) No role entry for "wiki" in module "docutils.parsers.rst.languages.en".
peru_user_guide/index.rst:43: (ERROR/3) Unknown interpreted text role "wiki".
peru_user_guide/index.rst:49: (INFO/1) No role entry for "wiki" in module "docutils.parsers.rst.languages.en".
peru_user_guide/index.rst:49: (ERROR/3) Unknown interpreted text role "wiki".
peru_user_guide/index.rst:25: (ERROR/3) Undefined substitution referenced: "build".
peru_user_guide/index.rst:25: (ERROR/3) Unknown target name: "build".
```

