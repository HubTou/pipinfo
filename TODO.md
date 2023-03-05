# Ideas for improvement and evolution

## Bugs to be fixed
* Handling multiple extra variables in a requirement line. For example:
  ```
  Requires-Dist: pipreqs ; extra == "pipfile-deprecated-finder" or extra == "requirements-deprecated-finder"
  ```

## Limitations to be removed
* Processing dependencies conditions, including testing variables such as:
  os_name, platform_python_implementation, platform_system, sys_platform, python_version, python_full_version, implementation_name
* Handling variations in package dependencies with '-' and '_' characters

## New features
* Printing the first level of package dependencies (-d|--depends-on)
* Printing the first level of package requirements (-r|--required-by)
* Expanding the 2 previous prints to a tree (-t|--tree)

## Other possible features
* Checking dependencies on system (FreeBSD for a start) packages
* Checking the integrity of installed packages (missing or modified files)
* Checking the dependencies of installed packages (missing dependencies or wrong versions)
* Wrapping long lines (-w|--wrap)
