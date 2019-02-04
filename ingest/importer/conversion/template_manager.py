import copy
import logging
import re

from openpyxl.worksheet import Worksheet

import ingest.template.schema_template as schema_template
from ingest.api.ingestapi import IngestApi
from ingest.importer.conversion import utils, conversion_strategy
from ingest.importer.conversion.column_specification import ColumnSpecification
from ingest.importer.conversion.conversion_strategy import CellConversion, \
    FieldOfSingleElementListCellConversion
from ingest.importer.conversion.metadata_entity import MetadataEntity
from ingest.importer.data_node import DataNode
from ingest.template.schema_template import SchemaTemplate

MODULE_TAB_TITLE_PATTERN = re.compile(r'^(?P<main_label>\w+)( - \w+)?')


class TemplateManager:

    def __init__(self, template:SchemaTemplate, ingest_api:IngestApi):
        self.template = template
        self.ingest_api = ingest_api
        self.logger = logging.getLogger(__name__)

    def create_template_node(self, worksheet: Worksheet):
        concrete_entity = self.get_concrete_entity_of_tab(worksheet.title)
        schema = self._get_schema(concrete_entity)
        data_node = DataNode()
        data_node['describedBy'] = schema['url']
        data_node['schema_type'] = schema['domain_entity']
        return data_node

    def create_row_template(self, worksheet: Worksheet):
        tab_name = worksheet.title
        object_type = self.get_concrete_entity_of_tab(tab_name)
        header_row = self.get_header_row(worksheet)
        cell_conversions = []

        header_counter = {}
        for cell in header_row:
            header = cell.value

            if not header_counter.get(header):
                header_counter[header] = 0
            header_counter[header] = header_counter[header] + 1

            column_spec = self._define_column_spec(header, object_type,
                                                   order_of_occurence=header_counter[header])
            strategy = conversion_strategy.determine_strategy(column_spec)
            cell_conversions.append(strategy)

        default_values = self._define_default_values(object_type)
        return RowTemplate(cell_conversions, default_values=default_values)

    def create_simple_row_template(self, worksheet: Worksheet):
        tab_name = worksheet.title
        object_type = self.get_concrete_entity_of_tab(tab_name)
        header_row = self.get_header_row(worksheet)

        cell_conversions = []
        for cell in header_row:
            header = cell.value
            column_spec = self._define_column_spec(header, object_type)
            strategy = FieldOfSingleElementListCellConversion(column_spec.field_name,
                                                 column_spec.determine_converter())
            cell_conversions.append(strategy)

        default_values = self._define_default_values(object_type)
        return RowTemplate(cell_conversions, default_values=default_values)

    # TODO move this outside template manager
    @staticmethod
    def get_header_row(worksheet):
        for row in worksheet.iter_rows(row_offset=3, max_row=1):
            header_row = row

        clean_header_row = []

        for cell in header_row:
            if cell.value is None:
                continue
            clean_header_row.append(cell)

        return clean_header_row

    def _define_column_spec(self, header, object_type, order_of_occurence=1):
        if header is not None:
            parent_path, __ = utils.split_field_chain(header)
            raw_spec = self.lookup(header)
            raw_parent_spec = self.lookup(parent_path)
            concrete_type = utils.extract_root_field(header)
            main_category = self.get_domain_entity(concrete_type)
            column_spec = ColumnSpecification.build_raw(header, object_type, main_category, raw_spec,
                                                        parent=raw_parent_spec,
                                                        order_of_occurence=order_of_occurence)
        else:
            column_spec = None
        return column_spec

    def _define_default_values(self, object_type):
        default_values = {
            'describedBy': self.get_schema_url(object_type),
            'schema_type': self.get_domain_entity(object_type)
        }
        return default_values

    def get_latest_schema_url(self, high_level_entity, domain_entity, concrete_entity):
        latest_schema = self.ingest_api.get_schemas(
            latest_only=True,
            high_level_entity=high_level_entity,
            domain_entity=domain_entity.split('/')[0],
            concrete_entity=concrete_entity
        )

        return latest_schema[0]['_links']['json-schema']['href'] if latest_schema else None

    def get_schema_url(self, concrete_entity):
        schema = self._get_schema(concrete_entity)
        # TODO use schema version that is specified in spreadsheet for now
        return schema.get('url') if schema else None

    # TODO this just 2 lines. Perhaps we can just inline this to client code?
    def _get_schema(self, concrete_entity):
        spec = self.lookup(concrete_entity)
        return spec.get('schema') if spec else None

    def get_concrete_entity_of_tab(self, tab_name):
        result = MODULE_TAB_TITLE_PATTERN.search(tab_name)
        if not result:
            raise InvalidTabName(tab_name)
        main_label = result.group('main_label')
        return self.template.get_tab_key(main_label)

    def get_domain_entity(self, concrete_type):
        """
        Domain Entity is the high level classification of Concrete Entities. For example,
        Donor Organism belongs to the Biomaterial domain; all Donor Organisms are considered
        Biomaterials.

        :param concrete_type: the actual metadata entity type
        :return: the domain entity for the given concrete_entity
        """
        domain_entity = None
        spec = self.lookup(concrete_type)
        schema = spec.get('schema') if spec else None
        if schema:
            domain_entity = schema.get('domain_entity', '')
            subdomain = domain_entity.split('/')
            if subdomain:
                domain_entity = subdomain[0]
        return domain_entity

    def get_key_for_label(self, header_name, tab_name):
        try:
            key = self.template.get_key_for_label(header_name, tab_name)
        except:
            self.logger.warning(f'{header_name} in "{tab_name}" tab is not found in schema template')
        return key

    def lookup(self, header_name):
        try:
            spec = self.template.lookup(header_name)
        except schema_template.UnknownKeyException:
            self.logger.warning(f'schema_template.UnknownKeyException: Could not lookup {header_name} in template.')
            return {}

        return spec


def build(schemas, ingest_api) -> TemplateManager:
    template = None

    if not schemas:
        template = SchemaTemplate(ingest_api_url=ingest_api.url)
    else:
        template = SchemaTemplate(ingest_api_url=ingest_api.url, list_of_schema_urls=schemas)

    template_mgr = TemplateManager(template, ingest_api)
    return template_mgr


class RowTemplate:

    def __init__(self, cell_conversions, default_values={}):
        self.cell_conversions = cell_conversions
        self.default_values = copy.deepcopy(default_values)

    def do_import(self, row):
        metadata = MetadataEntity(content=self.default_values)
        for index, cell in enumerate(row):
            if cell.value is None:
                continue
            conversion: CellConversion = self.cell_conversions[index]
            conversion.apply(metadata, cell.value)
        return metadata


class ParentFieldNotFound(Exception):
    def __init__(self, header_name):
        message = f'{header_name} has no parent field'
        super(ParentFieldNotFound, self).__init__(message)

        self.header_name = header_name


# TODO there's another exception with this name; change this (or that) #module-tab
class InvalidTabName(Exception):

    def __init__(self, tab_name):
        super(InvalidTabName, self).__init__(f'Invalid tab name [{tab_name}]')
        self.tab_name = tab_name
