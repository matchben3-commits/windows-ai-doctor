"""Allowlisted cmd-shim 8.0.0 output, never interpreted or executed.

Templates adapted from npm/cmd-shim (ISC); see THIRD_PARTY_NOTICES.md.
Only the no-extra-arguments Node and direct-native forms are supported.
"""


def templates(marker, *, node=True):
    """Return complete known wrappers for one validated relative package bin."""
    batch_target = '"%dp0%\\' + marker.replace('/', '\\') + '"'
    shell_target = '"$basedir/' + marker + '"'
    head = """@ECHO off
GOTO start
:find_dp0
SET dp0=%~dp0
EXIT /b
:start
SETLOCAL
CALL :find_dp0
"""
    cmd = head + ("""
IF EXIST "%dp0%\\node.exe" (
  SET "_prog=%dp0%\\node.exe"
) ELSE (
  SET "_prog=node"
  SET PATHEXT=%PATHEXT:;.JS;=;%
)

endLocal & goto #_undefined_# 2>NUL || title %COMSPEC% & "%_prog%"  TARGET %*
""" if node else "TARGET   %*\n").replace("TARGET", batch_target)
    sh = r'''#!/bin/sh
basedir=$(dirname "$(echo "$0" | sed -e 's,\\,/,g')")

case `uname` in
    *CYGWIN*|*MINGW*|*MSYS*)
        if command -v cygpath > /dev/null 2>&1; then
            basedir=`cygpath -w "$basedir"`
        fi
    ;;
esac

'''
    sh += ('''if [ -x "$basedir/node" ]; then
  exec "$basedir/node"  TARGET "$@"
else 
  exec node  TARGET "$@"
fi
''' if node else 'exec TARGET   "$@"\n').replace("TARGET", shell_target)
    ps = '''#!/usr/bin/env pwsh
$basedir=Split-Path $MyInvocation.MyCommand.Definition -Parent

$exe=""
if ($PSVersionTable.PSVersion -lt "6.0" -or $IsWindows) {
  # Fix case when both the Windows and Linux builds of Node
  # are installed in the same directory
  $exe=".exe"
}
'''
    ps += ('''$ret=0
if (Test-Path "$basedir/node$exe") {
  # Support pipeline input
  if ($MyInvocation.ExpectingInput) {
    $input | & "$basedir/node$exe"  TARGET $args
  } else {
    & "$basedir/node$exe"  TARGET $args
  }
  $ret=$LASTEXITCODE
} else {
  # Support pipeline input
  if ($MyInvocation.ExpectingInput) {
    $input | & "node$exe"  TARGET $args
  } else {
    & "node$exe"  TARGET $args
  }
  $ret=$LASTEXITCODE
}
exit $ret
''' if node else '''# Support pipeline input
if ($MyInvocation.ExpectingInput) {
  $input | & TARGET   $args
} else {
  & TARGET   $args
}
exit $LASTEXITCODE
''').replace("TARGET", shell_target)
    return {".cmd": cmd, ".ps1": ps, "": sh}


def known_wrapper(content, suffix, marker, *, node):
    expected = templates(marker, node=node).get(suffix.lower())
    if expected is None:
        return False

    def normalized(text):
        # Blank lines, indentation and CRLF/LF do not change these templates.
        # Preserve all commands, comments, quoting and interior whitespace.
        return "\n".join(line.strip(" \t") for line in text.replace("\r\n", "\n").split("\n")
                         if line.strip(" \t"))

    return normalized(content) == normalized(expected)
