## Special Case: Combined Substitution and Link References

We need to update this module to handle the particularly tricky case of combined substitution and link reference pattern like `|build|_`. This is a common pattern in Sphinx documentation where a substitution is used as the text of a link. When this pattern is used, docutils reports two errors:

1. Undefined substitution referenced: "build"
2. Unknown target name: "build"

Both errors occur on the same line and reference the same name.

Note: There is a conf.py file at the root of this repo, but that is not what we are concerned with; that is for the documentation in this repo. I am concerned with the conf.py files that are generated for BTDocs packages, like the one at `~/workplace/Brazil-test/src/BTDocs-Brazil` that I am using for testing.

### Example

The following code block is and example RST file:
```
.. Copyright © 2024, Amazon, LLC.

   ** Contributions are always welcome! **

   For information about editing or updating this file, see:
   https://builderhub.corp.amazon.com/docs/contributing.html

   For Builder Tools' writing, formatting and style guidelines, see:
   https://btdocs.builder-tools.aws.dev/writing/

###############
Peru User Guide
###############

.. contents::
   :local:

Welcome to the Peru User Guide!

.. _concepts-peru:

What is Peru?
=============

Peru is a long-term project to reboot and modernize Amazon's code base, while retaining the
advantages of today's Builder Tools infrastructure. In particular, the Peru code base is built upon
existing Brazil tools, commands, and services, which have been updated to support Peru's new
capabilities. To a large degree, you work with Peru packages, version sets, and workspaces in the
same way you work with those of "classic" Brazil code base: you still use the :doc:`brazil CLI
<brazilcli:index>`, submit code reviews with :doc:`crux:index`, build on |build|_, and deploy
through :doc:`pipelines:index`.

This is a |bogus| text substitution.

This is a |bogus|_ text substitution with a link.

.. _peru-goals:

Peru's goals
============
```

Here are the errors rstcheck produces:
```
(.venv) ericn@ericn-mac: ~/workplace/Brazil-test/src/BTDocs-Brazil % rstcheck peru_user_guide/index.rst
peru_user_guide/index.rst:25: (ERROR/3) Undefined substitution referenced: "build".
peru_user_guide/index.rst:33: (ERROR/3) Undefined substitution referenced: "bogus".
peru_user_guide/index.rst:35: (ERROR/3) Undefined substitution referenced: "bogus".
peru_user_guide/index.rst:25: (ERROR/3) Unknown target name: "build".
peru_user_guide/index.rst:35: (ERROR/3) Unknown target name: "bogus".
Error! Issues detected.
```
The 'build' substitution and link target are defined in the docset's conf.py file, but that is not being passed to docutils properly. The 'bogus' link and target are not defined, so those should throw errors.

## Solution Requirements

The solution should:

1. Detect and load conf.py files from the directory tree of RST files being checked
2. Register custom roles, directives, substitutions, and link targets defined in conf.py with docutils
3. Handle the special case of combined substitution and link references (`|name|_`)
4. Not suppress legitimate errors for undefined elements that aren't defined in conf.py or the RST files

## Avoid Hardcoding Specific Names

A critical mistake to avoid is hardcoding specific names (like "build") in the code. The solution should be general and work for any project, not just specific cases. We cannot add anything to an allowlist that is not pulled from the Sphinx environment at run time.

## Testing Strategy

Test the solution with:

1. Regular undefined substitutions (should still report errors)
2. Regular undefined targets (should still report errors)
3. Combined substitution and link references defined in conf.py (should not report errors)
4. Combined substitution and link references not defined in conf.py (should report errors)

It's OK to write tests for the work you do, but before considering the task done, check with the user to test in their local virtual environment to see if the fix works there.