#!/usr/bin/env python3
""" pipinfo - Alternative tool for listing Python packages
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import json
import logging
import os
import pprint
import re
import sys
import time
import urllib.request

import bs4
import colorama
import packaging
import packaging.utils
import tqdm


####################################################################################################
def get_site_package_dirs():
    """ Returns a dictionary of site-packages directories in the Python PATH """
    site_packages_dirs = {}

    # Location where system-wide packages are installed
    if os.name == 'nt':
        system_prefix = f"{sys.base_prefix}" + os.sep + "Lib"
    else: # os.name == 'posix':
        system_prefix = f"{sys.base_prefix}" + os.sep + "lib" \
                        + os.sep + f"python{sys.version_info[0]}.{sys.version_info[1]}"

    # We search for "site-package" directories in the Python PATH
    for directory in sys.path:
        if directory.endswith('site-packages'):
            if directory.startswith(system_prefix):
                site_packages_dirs[directory] = 'system'
            else:
                site_packages_dirs[directory] = 'user'

    return site_packages_dirs


####################################################################################################
def process_requires_file(filename, requires, extras):
    """ Loads requires and extras from a .egg-info/requires.txt file """
    with open(filename, encoding="utf-8", errors="ignore") as file:
        lines = file.readlines()

    logging.debug("Processing file: %s", filename)
    extra = ""
    extra_conditions = ""
    for line in lines:
        line = line.strip()
        if line:
            logging.debug(line)

            # Handling extra lines (ie. [extra] or [extra:conditions])
            if line[0] == '[':
                line = re.sub(r"^ *\[", "", line)
                line = re.sub(r"\] *$", "", line)
                parts = line.split(":")
                extra = parts[0]
                if len(parts) > 1:
                    extra_conditions = parts[1]
                else:
                    extra_conditions = ""
                if extra and extra not in extras:
                    extras[extra] = {}

            # Handling requirements lines
            else:
                dependency = re.sub(r"[ ;!~<=>].*$", "", line)
                if '[' in dependency:
                    conditions = re.sub(r"^.*] *;* *", "", line)
                else:
                    conditions = re.sub(r"^" + dependency + " *;* *", "", line)
                if extra:
                    if dependency in extras[extra]:
                        if conditions:
                            extras[extra][dependency] += ";" + conditions
                        if extra_conditions:
                            extras[extra][dependency] += ";" + extra_conditions
                    else:
                        extras[extra][dependency] = {}
                        if conditions:
                            extras[extra][dependency] = conditions
                        if extra_conditions:
                            if extras[extra][dependency]:
                                extras[extra][dependency] += ";" + extra_conditions
                            else:
                                extras[extra][dependency] = extra_conditions
                else:
                    if dependency in requires:
                        if conditions:
                            requires[dependency] += ";" + conditions
                        if extra_conditions:
                            requires[dependency] += ";" + extra_conditions
                    else:
                        requires[dependency] = {}
                        if conditions:
                            requires[dependency] = conditions
                        if extra_conditions:
                            if requires[dependency]:
                                requires[dependency] += ";" + extra_conditions
                            else:
                                requires[dependency] = extra_conditions

    logging.debug("requires:\n%s", pprint.pformat(requires))
    logging.debug("extras:\n%s", pprint.pformat(extras))

    return requires, extras


####################################################################################################
def get_info_from_site_packages_dir(directory, directory_type):
    """ Returns a list of packages information from {dist, egg}-info sub-directories """
    info = []

    # A dictionary to store package/version that we have already been processed
    # (some packages provide both a .dist-info and .egg-info directory)
    deja_vu = {}

    with os.scandir(directory) as items:
        for item in items:
            if item.is_dir() \
            and (item.name.endswith('.dist-info') or item.name.endswith('.egg-info')):
                package_dir = directory + os.sep + item.name

                if item.name.endswith('.dist-info'):
                    metadata_file = package_dir + os.sep + 'METADATA'
                    requires_file = ""
                elif item.name.endswith('.egg-info'):
                    metadata_file = package_dir + os.sep + 'PKG-INFO'
                    requires_file = package_dir + os.sep + 'requires.txt'

                if not os.path.isfile(metadata_file):
                    logging.info("'%s' does not exist!", metadata_file)
                else:
                    with open(metadata_file, encoding="utf-8", errors="ignore") as file:
                        lines = file.readlines()

                    logging.debug("Processing file: %s", metadata_file)
                    name = ""
                    version = ""
                    summary = ""
                    requires = {}
                    extras = {}
                    for line in lines:
                        line = line.strip()
                        if line.startswith("Metadata-Version: "):
                            if line != 'Metadata-Version: 2.1':
                                logging.info("'%s' has '%s'", metadata_file, line)
                        elif line.startswith("Name: "):
                            name = re.sub(r"^Name: ", "", line)
                        elif line.startswith("Version: "):
                            version = re.sub(r"^Version: ", "", line)
                        elif line.startswith("Summary: "):
                            summary = re.sub(r"^Summary: ", "", line)

                        elif line.startswith("Requires-Dist: "):
                            logging.debug(line)

                            line = re.sub(r"^Requires-Dist: ", "", line)
                            dependency = re.sub(r"[ ;!~<=>].*", "", line)
                            if '[' in dependency:
                                conditions = re.sub(r"^.*] *;* *", "", line)
                            else:
                                conditions = re.sub(r"^" + dependency + " *;* *", "", line)

                            if "extra == " in line:
                                for part in conditions.split("extra == ")[1:]:
                                    extra = re.sub(r"['\"].*", "", part[1:])

                                    # Remove the extra == "NAME" from the conditions
                                    conditions = re.sub(r" *;* *extra == ." + extra + ". *",
                                                        ";", conditions)
                                    conditions = re.sub(r" *and *;", "", conditions)
                                    conditions = re.sub(r";and *", ";", conditions)
                                    conditions = re.sub(r";$", "", conditions)

                                    if extra not in extras:
                                        extras[extra] = {}
                                    if dependency in extras[extra]:
                                        if conditions:
                                            extras[extra][dependency] += ";" + conditions
                                    else:
                                        extras[extra][dependency] = conditions
                            else:
                                if dependency in requires:
                                    if conditions:
                                        requires[dependency] += ";" + conditions
                                else:
                                    requires[dependency] = conditions
                        elif line.startswith("Home-page: "):
                            pass
                        elif line.startswith("Project-URL: "):
                            pass
                        elif line.startswith("Download-URL: "):
                            pass
                        elif line.startswith("Author: "):
                            pass
                        elif line.startswith("Author-email: "):
                            pass
                        elif line.startswith("Maintainer: "):
                            pass
                        elif line.startswith("Maintainer-email: "):
                            pass
                        elif line.startswith("License: "):
                            pass
                        elif line.startswith("License-Expression: "):
                            pass
                        elif line.startswith("License-File: "):
                            pass
                        elif line.startswith("Platform: "):
                            pass
                        elif line.startswith("Requires-Python: "):
                            pass
                        elif line.startswith("Keywords: "):
                            pass
                        elif line.startswith("Classifier: "):
                            pass
                        elif line.startswith("Description-Content-Type: "):
                            pass
                        elif line.startswith("Provides: "):
                            pass
                        elif line.startswith("Provides-Extra: "):
                            pass
                        elif not line:
                            # The unstructured description begins. We can stop here
                            break
                        else:
                            logging.info("'%s' has unknown '%s'", metadata_file, line)

                    logging.debug("requires:\n%s", pprint.pformat(requires))
                    logging.debug("extras:\n%s", pprint.pformat(extras))

                    # egg-info entries store requirements in a separate file
                    if requires_file and os.path.isfile(requires_file):
                        requires, extras = process_requires_file(requires_file, requires, extras)

                    # Some packages provide both a .dist-info and .egg-info directory
                    # so let's avoid duplicates
                    if not (name in deja_vu and version in deja_vu[name]):
                        info.append(
                            {
                                "directory": package_dir,
                                "type": directory_type,
                                "name": name,
                                "version": version,
                                "summary": summary,
                                "requires": requires,
                                "extras": extras,
                            }
                        )
                        if name not in deja_vu:
                            deja_vu[name] = {}
                        if version not in deja_vu[name]:
                            deja_vu[name][version] = True

    return info


####################################################################################################
def get_user_and_system_packages():
    """ Returns lists of user and system packages """
    user_packages = []
    system_packages = []

    site_packages_dirs = get_site_package_dirs()

    for directory, value in site_packages_dirs.items():
        packages = get_info_from_site_packages_dir(directory, value)
        if value == 'user':
            if not user_packages:
                user_packages = packages
            else:
                user_packages += packages
        else: # if site_packages_dirs[directory] == 'system':
            if not system_packages:
                system_packages = packages
            else:
                system_packages += packages

    return user_packages, system_packages


####################################################################################################
def get_packages_list_max_sizes(packages):
    """ Returns the maximum width of name/version/summary columns for a packages list """
    longuest_name = len('Package')
    longuest_version = len('Version')
    longuest_summary = len('Summary')

    for package in packages:
        name = package['name']
        length = len(name)
        if length > longuest_name:
            longuest_name = length

        version = package['version']
        length = len(version)
        if length > longuest_version:
            longuest_version = length

        summary = package['summary']
        length = len(summary)
        if length > longuest_summary:
            longuest_summary = length

    return longuest_name, longuest_version, longuest_summary


####################################################################################################
def get_unique_packages(packages):
    """ Returns a dictionary of unique packages with appearances count """
    unique_packages = {}

    for package in packages:
        name = package['name']
        if name in unique_packages:
            unique_packages[name] += 1
        else:
            unique_packages[name] = 1

    return unique_packages


####################################################################################################
def get_caching_directory():
    """ Find and create a directory to save cached files """
    directory = ''

    if os.name == 'nt':
        if 'LOCALAPPDATA' in os.environ:
            directory = os.environ['LOCALAPPDATA'] + os.sep + "cache" + os.sep + "pipinfo"
        elif 'TMP' in os.environ:
            directory = os.environ['TMP'] + os.sep + "cache" + os.sep + "pipinfo"

    else: # os.name == 'posix':
        if 'HOME' in os.environ:
            directory = os.environ['HOME'] + os.sep + ".cache" + os.sep + "pipinfo"
        elif 'TMPDIR' in os.environ:
            directory = os.environ['TMPDIR'] + os.sep + ".cache" + os.sep + "pipinfo"
        elif 'TMP' in os.environ:
            directory = os.environ['TMP'] + os.sep + ".cache" + os.sep + "pipinfo"

    if directory:
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError:
            directory = ''

    return directory


####################################################################################################
def get_package_latest_version(package_name):
    """ Get the last available version for a package """
    caching_dir = get_caching_directory()
    caching_file = ''
    if caching_dir:
        caching_file = f"{caching_dir}" + os.sep + f"{package_name}.html"

    # If there's a caching file of less than 1 day, read it instead of using the Web service
    if caching_file \
    and os.path.isfile(caching_file) \
    and (time.time() - os.path.getmtime(caching_file)) < 24 * 60 * 60:
        with open(caching_file, "rb") as file:
            html = file.read()
    else:
        # Using the Pypi Legacy API / Simple Project API
        # See https://warehouse.pypa.io/api-reference/legacy.html
        url = f'https://pypi.org/simple/{package_name}/'
        try:
            with urllib.request.urlopen(url) as http:
                html = http.read()
        except urllib.error.HTTPError as error:
            logging.warning("Error while fetching '%s': %s", url, error)
            if error == 'HTTP Error 404: Not Found':
                # Let's write an empty file to avoid retrying later...
                if caching_file:
                    with open(caching_file, "wb") as file:
                        pass
            return ''

        if caching_file:
            with open(caching_file, "wb") as file:
                file.write(html)

    # Fetching the last filename of the page
    soup = bs4.BeautifulSoup(html.decode('utf-8'), features='html5lib')
    a_href_elements = soup.select('a')
    last_filename = a_href_elements[-1].getText()

    # Getting the version from the filename
    if last_filename.endswith(".whl"):
        _, latest_version, _, _ = packaging.utils.parse_wheel_filename(last_filename)
    else:
        _, latest_version = packaging.utils.parse_sdist_filename(last_filename)

    return str(latest_version)


####################################################################################################
def get_packages_latest_version(packages, progress_meter=True):
    """ Get the last available versions for a packages list """
    latest_versions = {}

    if progress_meter:
        print("Fetching packages latest version numbers from the Python Package Index...")
        for i in tqdm.tqdm(range(len(packages))):
            name = packages[i]['name']
            if name not in latest_versions:
                last_version = get_package_latest_version(name)
                latest_versions[name] = last_version
        print()
    else:
        for package in packages:
            name = package['name']
            if name not in latest_versions:
                last_version = get_package_latest_version(name)
                latest_versions[name] = last_version

    return latest_versions


####################################################################################################
def is_package_outdated(package, latest_versions):
    """ Returns True if the package is outdated """
    if not latest_versions[package['name']]:
        return False

    return packaging.version.parse(package['version']) \
           < packaging.version.parse(latest_versions[package['name']])


####################################################################################################
def get_package_vulnerabilities(package_name, package_version):
    """ Get the known vulnerabilities for a given package name and version """
    caching_dir = get_caching_directory()
    caching_file = ''
    if caching_dir:
        caching_file = f"{caching_dir}" + os.sep + f"{package_name}-{package_version}.json"

    # If there's a caching file of less than 1 day, read it instead of using the Web service
    if caching_file \
    and os.path.isfile(caching_file) \
    and (time.time() - os.path.getmtime(caching_file)) < 24 * 60 * 60:
        with open(caching_file, "rb") as file:
            json_data = file.read()
    else:
        # Using the Pypi JSON API / Release API
        # See https://warehouse.pypa.io/api-reference/json.html#release
        url = f'https://pypi.org/pypi/{package_name}/{package_version}/json'
        try:
            with urllib.request.urlopen(url) as http:
                json_data = http.read()
        except urllib.error.HTTPError as error:
            logging.warning("Error while fetching '%s': %s", url, error)
            if error == 'HTTP Error 404: Not Found':
                # Let's write an empty file to avoid retrying later...
                if caching_file:
                    with open(caching_file, "wb") as file:
                        pass
            return {}

        if caching_file:
            with open(caching_file, "wb") as file:
                file.write(json_data)

    data = json.loads(json_data)

    return data['vulnerabilities']


####################################################################################################
def get_packages_vulnerabilities(packages, progress_meter=True):
    """ Get the known vulnerabilities for a packages list """
    vulnerabilities = {}

    if progress_meter:
        print("Fetching packages known vulnerabilities from the Python Package Index...")
        for i in tqdm.tqdm(range(len(packages))):
            name = packages[i]['name']
            version = packages[i]['version']
            package_vulnerabilities = get_package_vulnerabilities(name, version)
            if package_vulnerabilities:
                if name not in vulnerabilities:
                    vulnerabilities[name] = {}
                    vulnerabilities[name][version] = package_vulnerabilities
                elif version not in vulnerabilities[name]:
                    vulnerabilities[name][version] = package_vulnerabilities
        print()
    else:
        for package in packages:
            name = package['name']
            version = package['version']
            package_vulnerabilities = get_package_vulnerabilities(name, version)
            if package_vulnerabilities:
                if name not in vulnerabilities:
                    vulnerabilities[name] = {}
                    vulnerabilities[name][version] = package_vulnerabilities
                elif version not in vulnerabilities[name]:
                    vulnerabilities[name][version] = package_vulnerabilities

    return vulnerabilities


####################################################################################################
def is_package_vulnerable(package, vulnerabilities):
    """ Returns True if the package is vulnerable """
    return package['name'] in vulnerabilities \
           and package['version'] in vulnerabilities[package['name']]


####################################################################################################
def get_packages_required_by(packages):
    """ Returns a dictionary of packages which are required by others """
    required_by = {}
    extras = {}

    # All comparisons are done case insensitive as packages are usually not precise...
    for package in packages:
        name = package['name'].lower()
        for dependency in package['requires']:
            dependency = dependency.lower()
            # A dependency can reference packages options ("extras") within brackets
            if '[' in dependency:
                extra = re.sub(r".*\[", "", dependency)
                extra = re.sub(r"].*", "", extra)
                dependency = re.sub(r"\[.*", "", dependency)
                # Several comma-separated extras can be specified
                for part in extra.split(','):
                    if dependency in extras:
                        if part not in extras[dependency]:
                            extras[dependency].append(part)
                    else:
                        extras[dependency] = [part]

            """ TODO The dependency conditions are not considered as of now
            Variables seen:
                os_name
                    from: os.name
                    values: 'nt', 'posix'
                platform_python_implementation
                    from: platform.python_implementation()
                    values: 'CPython', 'PyPy'
                platform_system
                    from: platform.system()
                    values: 'Windows', 'FreeBSD'
                sys_platform
                    from: sys.platform
                    values: 'linux', 'win32', 'freebsd13'
                python_version
                    from: platform.python_version_tuple()[0] + '.' + platform.python_version_tuple()[1]
                    values: '2.7', '3', '3.9'
                python_full_version
                    from: platform.python_version()
                    values: '3.9.16'
                implementation_name
                    from: sys.implementation.name
                    values: 'cpython'
            """
            if dependency in required_by:
                if name not in required_by[dependency]:
                    required_by[dependency].append(name)
            else:
                required_by[dependency] = [name]

    # If we have encountered extras, let's try to add their new dependencies
    while extras:
        key = list(extras.keys())[0]
        value = extras[key]

        for package in packages:
            name = package['name'].lower()
            if key == name:
                for extra in value:
                    if extra in package['extras']:
                        for dependency in package['extras'][extra]:
                            dependency = dependency.lower()
                            # A dependency can reference packages options ("extras") within brackets
                            if '[' in dependency:
                                newextra = re.sub(r".*\[", "", dependency)
                                newextra = re.sub(r"].*", "", newextra)
                                dependency = re.sub(r"\[.*", "", dependency)
                                # Several comma-separated extras can be specified
                                for part in newextra.split(','):
                                    if dependency in extras:
                                        if part not in extras[dependency]:
                                            extras[dependency].append(part)
                                    else:
                                        extras[dependency] = [part]

                            if dependency in required_by:
                                if name not in required_by[dependency]:
                                    required_by[dependency].append(name)
                            else:
                                required_by[dependency] = [name]

        del extras[key]

    return required_by


####################################################################################################
def is_package_required(package, required_by):
    """ Returns True if the package is vulnerable """
    return package['name'].lower() in required_by


####################################################################################################
def _case_insensitive_sort(element):
    """ Provides the criteria for case insensitive packages list sorting """
    return element['name'].lower()


####################################################################################################
def list_packages(packages, latest_versions, vulnerabilities, color=True, details=False):
    """ Prints installed packages list with summaries """
    longuest_name, longuest_version, longuest_summary = get_packages_list_max_sizes(packages)
    unique_packages = get_unique_packages(packages)

    outdated_count = 0
    vulnerable_count = 0
    if color:
        colorama.init()
    else:
        longuest_name += 2
        longuest_version += 2
    print(f"{'Package':{longuest_name}}" \
          + f" {'Version':{longuest_version}} {'Summary':{longuest_summary}}")
    print(f"{'-' * longuest_name} {'-' * longuest_version} {'-' * longuest_summary}")
    packages.sort(key=_case_insensitive_sort)
    for package in packages:
        outdated = False
        vulnerable = False

        name = f"{package['name']:{longuest_name}}"
        if unique_packages[package['name']] > 1:
            if color:
                name = colorama.Fore.YELLOW \
                       + f"{package['name']:{longuest_name}}" \
                       + colorama.Fore.WHITE
            else:
                name = f"{'*' + package['name'] + '*':{longuest_name}}"

        version = f"{package['version']:{longuest_version}}"
        if latest_versions:
            if is_package_outdated(package, latest_versions):
                outdated = True
                outdated_count += 1
                if color:
                    version = colorama.Fore.YELLOW + version + colorama.Fore.WHITE
                else:
                    version = f"{'^' + package['version'] + '^':{longuest_version}}"
        if vulnerabilities:
            if is_package_vulnerable(package, vulnerabilities):
                vulnerable = True
                vulnerable_count += 1
                if color:
                    version = colorama.Back.RED + version + colorama.Back.BLACK
                elif version.startswith('^'):
                    version = version.replace('^', '!')
                else:
                    version = f"{'!' + package['version'] + '!':{longuest_version}}"

        summary = f"{package['summary']:{longuest_summary}}"

        line = f"{name} {version} {summary}"
        if package['type'] == 'user':
            if color:
                line = colorama.Style.BRIGHT + line + colorama.Style.RESET_ALL
        print(line)

        if details:
            if outdated:
                print(colorama.Fore.GREEN \
                      + f" => Version {latest_versions[package['name']]} is available" \
                      + colorama.Fore.WHITE)
            if vulnerable:
                for vulnerability in vulnerabilities[package['name']][package['version']]:
                    print(colorama.Fore.RED, end='')
                    print(f" => {vulnerability['id']}:")
                    print(f"      Aliases: {vulnerability['aliases']}")
                    print(f"      Details: {vulnerability['details']}")
                    print(f"      Fixed in: {vulnerability['fixed_in']}")
                    print(f"      Link: {vulnerability['link']}")
                    print(f"      Source: {vulnerability['source']}")
                    print(f"      Summary: {vulnerability['summary']}")
                    print(f"      Withdrawn: {vulnerability['withdrawn']}", end='')
                    print(colorama.Fore.WHITE)

    print(f"{'=' * longuest_name}={'=' * longuest_version}={'=' * longuest_summary}")
    print(f"{len(packages)} package{'s'[:len(packages)^1]}", end='')
    if outdated_count:
        print(f", {outdated_count} outdated", end='')
    if vulnerable_count:
        print(f", {vulnerable_count} vulnerable", end='')
    print()
