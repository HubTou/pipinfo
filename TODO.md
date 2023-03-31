# Ideas for improvement and evolution

## Limitations to be removed
* Handling variations ('-' or '_' instead of the other one) in package dependencies

## New features
* Printing the first level of package dependencies (-d|--depends-on)
* Printing the first level of package requirements (-r|--required-by)
* Expanding the 2 previous prints to a tree (-t|--tree)
* Checking the integrity of installed packages (missing or modified files)
  * Checking modified files is possible for dist-info packages (with the RECORD file)
    but not for egg-info packages which only have list of files (in the SOURCES.txt file)
* Checking the dependencies of installed packages (missing dependencies or wrong versions)
* When checking vulnerabilities, using an orange background when a package has a
  vulnerability somewhere in its dependencies tree (a toolchain vulnerability)

## Other possible features
* Checking dependencies on system (FreeBSD for a start) packages
* Wrapping long lines (-w|--wrap)

