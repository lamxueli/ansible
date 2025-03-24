"""Generate XML code coverage reports."""

from __future__ import annotations

import os
import time

from xml.etree.ElementTree import (
    Comment,
    Element,
    SubElement,
    tostring,
)

from xml.dom import (
    minidom,
)

from ...io import (
    make_dirs,
    read_json_file,
)

from ...util_common import (
    ResultType,
    write_text_test_results,
)

from ...util import (
    get_ansible_version,
)

from ...data import (
    data_context,
)

from ...provisioning import (
    prepare_profiles,
)

from .combine import (
    combine_coverage_files,
    CoverageCombineConfig,
)

from . import (
    run_coverage,
)


def command_coverage_xml(args: CoverageXmlConfig) -> None:
    """Generate an XML coverage report."""
    host_state = prepare_profiles(args)  # coverage xml
    output_files = combine_coverage_files(args, host_state)

    for output_file in output_files:
        xml_name = '%s.xml' % os.path.basename(output_file)
        if output_file.endswith('-powershell'):
            report = _generate_powershell_xml(output_file)

            rough_string = tostring(report, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty = reparsed.toprettyxml(indent='    ')

            write_text_test_results(ResultType.REPORTS, xml_name, pretty)
        else:
            xml_path = os.path.join(ResultType.REPORTS.path, xml_name)
            make_dirs(ResultType.REPORTS.path)
            run_coverage(args, host_state, output_file, 'xml', ['-i', '-o', xml_path])


def _generate_powershell_xml(coverage_file: str) -> Element:
    """Generate a PowerShell coverage report XML element from the specified coverage file and return it."""
    coverage_info = read_json_file(coverage_file)

    content_root = data_context().content.root
    is_ansible = data_context().content.is_ansible

    packages: dict[str, dict[str, dict[str, int]]] = {}
    for path, results in coverage_info.items():
        filename = os.path.splitext(os.path.basename(path))[0]

        if filename.startswith('Ansible.ModuleUtils'):
            package = 'ansible.module_utils'
        elif is_ansible:
            package = 'ansible.modules'
        else:
            rel_path = path[len(content_root) + 1:]
            plugin_type = "modules" if rel_path.startswith("plugins/modules") else "module_utils"
            package = 'ansible_collections.%splugins.%s' % (data_context().content.collection.prefix, plugin_type)

        if package not in packages:
            packages[package] = {}

        packages[package][path] = results

    elem_coverage = Element('coverage')
    elem_coverage.append(
        Comment(' Generated by ansible-test from the Ansible project: https://www.ansible.com/ '))
    elem_coverage.append(
        Comment(' Based on https://raw.githubusercontent.com/cobertura/web/master/htdocs/xml/coverage-04.dtd '))

    elem_sources = SubElement(elem_coverage, 'sources')

    elem_source = SubElement(elem_sources, 'source')
    elem_source.text = data_context().content.root

    elem_packages = SubElement(elem_coverage, 'packages')

    total_lines_hit = 0
    total_line_count = 0

    for package_name, package_data in packages.items():
        lines_hit, line_count = _add_cobertura_package(elem_packages, package_name, package_data)

        total_lines_hit += lines_hit
        total_line_count += line_count

    elem_coverage.attrib.update({
        'branch-rate': '0',
        'branches-covered': '0',
        'branches-valid': '0',
        'complexity': '0',
        'line-rate': str(round(total_lines_hit / total_line_count, 4)) if total_line_count else "0",
        'lines-covered': str(total_line_count),
        'lines-valid': str(total_lines_hit),
        'timestamp': str(int(time.time())),
        'version': get_ansible_version(),
    })

    return elem_coverage


def _add_cobertura_package(packages: Element, package_name: str, package_data: dict[str, dict[str, int]]) -> tuple[int, int]:
    """Add a package element to the given packages element."""
    elem_package = SubElement(packages, 'package')
    elem_classes = SubElement(elem_package, 'classes')

    total_lines_hit = 0
    total_line_count = 0

    for path, results in package_data.items():
        lines_hit = len([True for hits in results.values() if hits])
        line_count = len(results)

        total_lines_hit += lines_hit
        total_line_count += line_count

        elem_class = SubElement(elem_classes, 'class')

        class_name = os.path.splitext(os.path.basename(path))[0]
        if class_name.startswith("Ansible.ModuleUtils"):
            class_name = class_name[20:]

        content_root = data_context().content.root
        filename = path
        if filename.startswith(content_root):
            filename = filename[len(content_root) + 1:]

        elem_class.attrib.update({
            'branch-rate': '0',
            'complexity': '0',
            'filename': filename,
            'line-rate': str(round(lines_hit / line_count, 4)) if line_count else "0",
            'name': class_name,
        })

        SubElement(elem_class, 'methods')

        elem_lines = SubElement(elem_class, 'lines')

        for number, hits in results.items():
            elem_line = SubElement(elem_lines, 'line')
            elem_line.attrib.update(
                hits=str(hits),
                number=str(number),
            )

    elem_package.attrib.update({
        'branch-rate': '0',
        'complexity': '0',
        'line-rate': str(round(total_lines_hit / total_line_count, 4)) if total_line_count else "0",
        'name': package_name,
    })

    return total_lines_hit, total_line_count


class CoverageXmlConfig(CoverageCombineConfig):
    """Configuration for the coverage xml command."""
