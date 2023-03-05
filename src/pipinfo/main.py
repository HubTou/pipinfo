#!/usr/bin/env python3
""" pipinfo - Alternative tool for listing Python packages
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import getopt
import logging
import os
import sys

import libpnu

from .library import get_info_from_site_packages_dir, get_user_and_system_packages, \
                     get_packages_latest_version, is_package_outdated, \
                     get_packages_vulnerabilities, is_package_vulnerable, \
                     get_packages_required_by, is_package_required, list_packages

# Version string used by the what(1) and ident(1) commands:
ID = "@(#) $Id: pipinfo - Alternative tool for listing Python packages v0.9.0 (March 5, 2023) by Hubert Tournier $"

# Default parameters. Can be overcome by environment variables, then command line options
parameters = {
    'Options': {
        'Check latest versions': False,     # -l | --check-versions
        'Check vulnerabilities': False,     # -v | --check-vulns
        },
    'Display': {
        'Color': True,                      # -c | --no-color
        'Progress meter': True,             # -p | --no-progress
        'Detailed info': False,             # -i | --info
        },
    'Selections': {
        'User': False,                      # -U | --user
        'System': False,                    # -S | --system
        'Outdated': False,                  # -O | --outdated
        'Latest': False,                    # -L | --latest | --uptodate
        'Vulnerable': False,                # -V | --vulnerable
        'Healthy': False,                   # -H | --healthy | --sane
        'Issues': False,                    # -I | --issues
        'Not required': False,              # -N | --not-required
        'Required': False,                  # -R | --required
        },
}


####################################################################################################
def _display_help():
    """ Display usage and help """
    #pylint: disable=C0301
    print("usage: pipinfo [--debug] [--help|-?] [--version]", file=sys.stderr)
    print("       [-l|--check-latest] [-v|--check-vulns]", file=sys.stderr)
    print("       [-c|--no-color] [-p|--no-progress] [-i|--info]", file=sys.stderr)
    print("       [-S|--system] [-U|--user] [-I|--issues]", file=sys.stderr)
    print("       [-O|--outdated] [-L|--latest|--uptodate]", file=sys.stderr)
    print("       [-V|--vulnerable] [-H|--healthy|--sane]", file=sys.stderr)
    print("       [-N|--not-required] [-R|--required]", file=sys.stderr)
    print("       [--] [directory ...]", file=sys.stderr)
    print("---[ OPTIONS ]-----------------------------------------------------------", file=sys.stderr)
    print("  -l|--check-latest      Check latest versions", file=sys.stderr)
    print("  -v|--check-vulns        Check vulnerabilities", file=sys.stderr)
    print("---[ DISPLAY ]-----------------------------------------------------------", file=sys.stderr)
    print("  -c|--no-color           Toggle off color output", file=sys.stderr)
    print("  -p|--no-progress        Toggle off progress meter", file=sys.stderr)
    print("  -i|--info               Print detailed info on versions & vulnerabilities", file=sys.stderr)
    print("---[ SELECTIONS ]--------------------------------------------------------", file=sys.stderr)
    print("  -H|--healthy|--sane     Select only healthy packages", file=sys.stderr)
    print("  -I|--issues             Select all packages with issues (-O & -V)", file=sys.stderr)
    print("  -L|--latest|--uptodate  Select only latest packages", file=sys.stderr)
    print("  -O|--outdated           Select only outdated packages", file=sys.stderr)
    print("  -S|--system             Select only system packages", file=sys.stderr)
    print("  -U|--user               Select only user packages", file=sys.stderr)
    print("  -N|--not-required       Select only not required packages", file=sys.stderr)
    print("  -R|--required           Select only required packages", file=sys.stderr)
    print("  -V|--vulnerable         Select only vulnerable packages", file=sys.stderr)
    print("---[ MISC ]--------------------------------------------------------------", file=sys.stderr)
    print("  --debug                 Enable debug mode", file=sys.stderr)
    print("  --help|-?               Print usage and this help message and exit", file=sys.stderr)
    print("  --version               Print version and exit", file=sys.stderr)
    print("  --                      Options processing terminator", file=sys.stderr)
    print(file=sys.stderr)
    #pylint: enable=C0301


####################################################################################################
#pylint: disable=W0613
def _handle_interrupts(signal_number, current_stack_frame):
    """ Prevent SIGINT signals from displaying an ugly stack trace """
    print(" Interrupted!\n", file=sys.stderr)
    sys.exit(0)
#pylint: enable=W0613


####################################################################################################
def _process_environment_variables():
    """ Process environment variables """
    #pylint: disable=C0103, W0602
    global parameters
    #pylint: enable=C0103, W0602

    if "PIPINFO_DEBUG" in os.environ:
        logging.disable(logging.NOTSET)

    logging.debug("_process_environment_variables(): parameters:")
    logging.debug(parameters)


####################################################################################################
def _process_command_line():
    """ Process command line options """
    #pylint: disable=C0103, W0602
    global parameters
    #pylint: enable=C0103, W0602

    # option letters followed by : expect an argument
    # same for option strings followed by =
    character_options = "cilpvHILNORSUV?"
    string_options = [
        "check-latest",
        "check-vulns",
        "debug",
        "healthy",
        "help",
        "info",
        "issues",
        "latest",
        "no-color",
        "no-progress",
        "not-required",
        "outdated",
        "required",
        "sane",
        "system",
        "uptodate",
        "user",
        "version",
        "vulnerable",
    ]

    try:
        options, remaining_arguments = getopt.getopt(
            sys.argv[1:], character_options, string_options
        )
    except getopt.GetoptError as error:
        logging.critical("Syntax error: %s", error)
        _display_help()
        sys.exit(1)

    for option, _ in options:

        if option == "--debug":
            logging.disable(logging.NOTSET)

        elif option in ("--help", "-?"):
            _display_help()
            sys.exit(0)

        elif option == "--version":
            print(ID.replace("@(" + "#)" + " $" + "Id" + ": ", "").replace(" $", ""))
            sys.exit(0)

        elif option in ("--no-color", "-c"):
            parameters['Display']['Color'] = False

        elif option in ("--info", "-i"):
            parameters['Display']['Detailed info'] = True

        elif option in ("--check-latest", "-l"):
            parameters['Options']['Check latest versions'] = True

        elif option in ("--no-progress", "-p"):
            parameters['Display']['Progress meter'] = False

        elif option in ("--check-vulns", "-v"):
            parameters['Options']['Check vulnerabilities'] = True

        elif option in ("--healthy", "--sane", "-H"):
            parameters['Options']['Check vulnerabilities'] = True
            parameters['Selections']['Healthy'] = True
            parameters['Selections']['Vulnerable'] = False
            parameters['Selections']['Issues'] = False

        elif option in ("--issues", "-I"):
            parameters['Options']['Check latest versions'] = True
            parameters['Options']['Check vulnerabilities'] = True
            parameters['Selections']['Issues'] = True
            parameters['Selections']['Outdated'] = False
            parameters['Selections']['Latest'] = False
            parameters['Selections']['Vulnerable'] = False
            parameters['Selections']['Healthy'] = False

        elif option in ("--latest", "--uptodate", "-L"):
            parameters['Options']['Check latest versions'] = True
            parameters['Selections']['Latest'] = True
            parameters['Selections']['Outdated'] = False
            parameters['Selections']['Issues'] = False

        elif option in ("--not-required", "-N"):
            parameters['Selections']['Not required'] = True
            parameters['Selections']['Required'] = False

        elif option in ("--outdated", "-O"):
            parameters['Options']['Check latest versions'] = True
            parameters['Selections']['Outdated'] = True
            parameters['Selections']['Latest'] = False
            parameters['Selections']['Issues'] = False

        elif option in ("--required", "-R"):
            parameters['Selections']['Required'] = True
            parameters['Selections']['Not required'] = False

        elif option in ("--system", "-S"):
            parameters['Selections']['System'] = True
            parameters['Selections']['User'] = False

        elif option in ("--user", "-U"):
            parameters['Selections']['User'] = True
            parameters['Selections']['System'] = False

        elif option in ("--vulnerable", "-V"):
            parameters['Options']['Check vulnerabilities'] = True
            parameters['Selections']['Vulnerable'] = True
            parameters['Selections']['Healthy'] = False
            parameters['Selections']['Issues'] = False

    logging.debug("_process_command_line(): parameters:")
    logging.debug(parameters)
    logging.debug("_process_command_line(): remaining_arguments:")
    logging.debug(remaining_arguments)

    return remaining_arguments


####################################################################################################
def main():
    """ The program's main entry point """
    program_name = os.path.basename(sys.argv[0])

    libpnu.initialize_debugging(program_name)
    libpnu.handle_interrupt_signals(_handle_interrupts)
    _process_environment_variables()
    arguments = _process_command_line()

    # Gather specified, user or system site packages
    packages = []
    if arguments:
        for argument in arguments:
            packages += get_info_from_site_packages_dir(argument, 'specified')
    else:
        user_packages, system_packages = get_user_and_system_packages()
        if parameters['Selections']['User']:
            packages = user_packages
        elif parameters['Selections']['System']:
            packages = system_packages
        else:
            packages = user_packages + system_packages

    # Possibly check for and filter latest versions
    latest_versions = {}
    if parameters['Options']['Check latest versions']:
        latest_versions = get_packages_latest_version(packages,
                                                      parameters['Display']['Progress meter'])

    if parameters['Selections']['Outdated']:
        packages = [x for x in packages if is_package_outdated(x, latest_versions)]
    elif parameters['Selections']['Latest']:
        packages = [x for x in packages if not is_package_outdated(x, latest_versions)]

    # Possibly check for and filter vulnerabilities
    vulnerabilities = {}
    if parameters['Options']['Check vulnerabilities']:
        vulnerabilities = get_packages_vulnerabilities(packages,
                                                       parameters['Display']['Progress meter'])

    if parameters['Selections']['Vulnerable']:
        packages = [x for x in packages if is_package_vulnerable(x, vulnerabilities)]
    elif parameters['Selections']['Healthy']:
        packages = [x for x in packages if not is_package_vulnerable(x, vulnerabilities)]

    if parameters['Selections']['Issues']:
        packages = [x for x in packages if is_package_outdated(x, latest_versions)
                                        or is_package_vulnerable(x, vulnerabilities)]

    # Possibly check for and filter requirements
    required_by = {}
    if parameters['Selections']['Required'] or parameters['Selections']['Not required']:
        required_by = get_packages_required_by(packages)

    if parameters['Selections']['Required']:
        packages = [x for x in packages if is_package_required(x, required_by)]
    elif parameters['Selections']['Not required']:
        packages = [x for x in packages if not is_package_required(x, required_by)]

    # Process the remaining packages list
    list_packages(
        packages,
        latest_versions,
        vulnerabilities,
        color=parameters['Display']['Color'],
        details=parameters['Display']['Detailed info'],
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
