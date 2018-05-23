import copy
import re

from openpyxl.worksheet import Worksheet

import ingest.template.schema_template as schema_template
from ingest.importer.conversion import utils, conversion_strategy
from ingest.importer.conversion.column_specification import ColumnSpecification
from ingest.importer.conversion.conversion_strategy import CellConversion
from ingest.importer.conversion.data_converter import ListConverter, DataType, CONVERTER_MAP
from ingest.importer.data_node import DataNode
from ingest.template.schema_template import SchemaTemplate


class TemplateManager:

    def __init__(self, template:SchemaTemplate):
        self.template = template

    def create_template_node(self, worksheet: Worksheet):
        concrete_entity = self.get_concrete_entity_of_tab(worksheet.title)
        schema = self._get_schema(concrete_entity)
        data_node = DataNode()
        data_node['describedBy'] = schema['url']
        data_node['schema_type'] = schema['domain_entity']
        return data_node

    def create_row_template(self, worksheet:Worksheet):
        header_row = self._get_header_row(worksheet)
        cell_conversions = []
        for cell in header_row:
            header = cell.value
            column_spec = self._define_column_spec(header)
            strategy = conversion_strategy.determine_strategy(column_spec)
            cell_conversions.append(strategy)
        return RowTemplate(cell_conversions)

    @staticmethod
    def _get_header_row(worksheet):
        for row in worksheet.iter_rows(row_offset=3, max_row=1):
            header_row = row
        return header_row

    def _define_column_spec(self, header):
        parent_path, __ = utils.split_field_chain(header)
        raw_spec = self.template.get_key_for_label(header)
        raw_parent_spec = self.template.get_key_for_label(parent_path)
        return ColumnSpecification.build_raw(header, raw_spec, parent=raw_parent_spec)

    def get_schema_url(self, concrete_entity):
        schema = self._get_schema(concrete_entity)
        # TODO must query schema endpoint in core to get the latest version
        return schema.get('url') if schema else None

    def get_domain_entity(self, concrete_entity):
        schema = self._get_schema(concrete_entity)
        domain_entity = schema.get('domain_entity') if schema else None

        match = re.search('(?P<domain_entity>\w+)(\/*)', domain_entity)
        domain_entity = match.group('domain_entity')

        return domain_entity

    def _get_schema(self, concrete_entity):
        spec = self.lookup(concrete_entity)
        return spec.get('schema') if spec else None

    def get_concrete_entity_of_tab(self, tab_name):
        try:
            tabs_config = self.template.get_tabs_config()
            concrete_entity = tabs_config.get_key_for_label(tab_name)
        except:
            print(f'No entity found for tab {tab_name}')
            return None
        return concrete_entity

    def get_key_for_label(self, header_name, tab_name):
        try:
            key = self.template.get_key_for_label(header_name, tab_name)
        except:
            print(f'{header_name} in "{tab_name}" tab is not found in schema template')
        return key

    def lookup(self, header_name):
        try:
            spec = self.template.lookup(header_name)
        except schema_template.UnknownKeyException:
            print(f'schema_template.UnknownKeyException: Could not lookup {header_name} in template.')
            return {}

        return spec


def build(schemas) -> TemplateManager:
    template = SchemaTemplate(schemas)
    template_mgr = TemplateManager(template)
    return template_mgr


class RowTemplate:

    def __init__(self, cell_conversions, default_values={}):
        self.cell_conversions = cell_conversions
        self.default_values = copy.deepcopy(default_values)

    def do_import(self, row):
        data_node = DataNode(defaults=self.default_values)
        for index, cell in enumerate(row):
            conversion:CellConversion = self.cell_conversions[index]
            conversion.apply(data_node, cell.value)
        return data_node.as_dict()


class ParentFieldNotFound(Exception):
    def __init__(self, header_name):
        message = f'{header_name} has no parent field'
        super(ParentFieldNotFound, self).__init__(message)

        self.header_name = header_name
