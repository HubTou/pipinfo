# Installation
Once you have installed [Python](https://www.python.org/downloads/) and its packages manager [pip](https://pip.pypa.io/en/stable/installation/),
depending on if you want only this tool, the full set of PNU tools, or PNU plus a selection of additional third-parties tools, use one of these commands:
```
pip install pnu-pipinfo
pip install PNU
pip install pytnix
```
# PIPINFO(1)

## NAME
pipinfo - Alternative tool for listing Python packages

## SYNOPSIS
**pipinfo**
\[-l|--check-latest\]
\[-v|--check-vulns\]
\[-c|--no-color\]
\[-p|--no-progress\]
\[-i|--info\]
\[-S|--system\]
\[-U|--user\]
\[-I|--issues\]
\[-O|--outdated\]
\[-L|--latest|--uptodate\]
\[-V|--vulnerable\]
\[-H|--healthy|--sane\]
\[-N|--not-required\]
\[-R|--required\]
\[--debug\]
\[--help|-?\]
\[--version\]
\[--\]
\[directory ...\]

## DESCRIPTION
The **pipinfo** utility provides an alternative to the "pip list", "pip list --outdated", "pip show" and "pip-audit" commands.

It shows all the available packages in the Python PATH (not just the latest version) or given directories (even for different Python versions), differenciates user and system-wide packages (user packages are written in bright style), show duplicate packages (name in yellow foreground, including user versions shadowing system ones), shows each package summary (avoiding the use of "pip show" to discover what a package is about), and prints the count of installed packages.

With the *-l|--check-latest* option, it will also use a Python Index Package web service to check for the latest versions available, using a simple color (version in yellow foreground) or visual scheme to show outdated packages and count them.

With the *-v|--check-vulns* option, it will also use another Python Index Package web service to check for known vulnerabilities in your packages versions, using a simple color (version in red background) or visual scheme to show vulnerable packages and count them.

The color or visual scheme should be enough to tell you to upgrade the indicated packages, however you can print additional details about new versions available and vulnerabilities with the *-i|--info* option.

You can disable the color output with the *-c|--no-color* option, and the progress meter with the *-p|--no-progress* option.

Finally you can restrict the list to the user or system packages, outdated or up-to-date packages, vulnerable or sane packages, required or not packages with the options in upper case.

The most useful one is probably the *-I|--issues* option which will select the outdated or vulnerable packages only.

### OPTIONS
Options | Use
------- | ---
-l\|--check-latest|Check latest versions
-v\|--check-vulns|Check vulnerabilities
-c\|--no-color|Toggle off color output
-p\|--no-progress|Toggle off progress meter
-i\|--info|Print detailed info on versions & vulnerabilities
-S\|--system|Select only system packages
-U\|--user|Select only user packages
-L\|--latest\|--uptodate|Select only latest packages (implies -l)
-O\|--outdated|Select only outdated packages (implies -l)
-H\|--healthy\|--sane|Select only healthy packages (implies -v)
-V\|--vulnerable|Select only vulnerable packages (implies -v)
-R\|--required|Select only required packages
-N\|--not-required|Select only not required packages
-I\|--issues|Select all packages with issues (-O & -V)
--debug|Enable debug mode
--help\|-?|Print usage and a short help message and exit
--version|Print version and exit
--|Options processing terminator

## ENVIRONMENT
The PIPINFO_DEBUG environment variable can be set to any value to enable debug mode.
It's mostly used to display and debug the package requirements read from the Python packages metadata files.

The *LOCALAPPDATA* and *TMP* environment variables under Windows, and *HOME*, *TMPDIR* and *TMP* environment variables
under other operating systems can influence the caching directory used.

## FILES
The **pipinfo** utility will attempt to maintain a caching directory for the web services it uses, where the individual files will be re-used within the next 24 hours.

This directory will be located in one of the following places:
* Windows:
  * %LOCALAPPDATA%\\cache\\pipinfo
  * %TMP%\\cache\\pipinfo
* Unix:
  * ${HOME}/.cache/pipinfo
  * ${TMPDIR}/.cache/pipinfo
  * ${TMP}/.cache/pipinfo

## EXIT STATUS
The **pipinfo** utility exits 0 on success, and >0 if an error occurs.

## EXAMPLES
Use the following command to print a package listing after checking for the existence of new versions or vulnerabilities:
```
pipinfo -lv
```

Use the following command to restrict the list to outdated and vulnerable packages with details but no progress meter:
```
pipinfo -Iip
```

## SEE ALSO
[pip](https://pypi.org/project/pip/),
[pip-audit](https://pypi.org/project/pip-audit/)

## STANDARDS
The **pipinfo** utility is not a standard UNIX command.

It tries to follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for [Python](https://www.python.org/) code.

## PORTABILITY
Tested OK under Windows.

## HISTORY
This implementation was made for the [PNU project](https://github.com/HubTou/PNU),
both for my personal convenience and also to investigate some pip issues with the *pip list --outdated* option.

## LICENSE
It is available under the [3-clause BSD license](https://opensource.org/licenses/BSD-3-Clause).

## AUTHORS
[Hubert Tournier](https://github.com/HubTou)

## CAVEATS
The conditions on package dependencies aren't taken into account (yet).
"pipinfo -N" will nonetheless give appoximately the same results than "pip list --not-required".

