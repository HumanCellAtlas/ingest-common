#!/usr/bin/env python
"""
Description goes here
"""
__author__ = "jupp"
__license__ = "Apache 2.0"
__date__ = "08/05/2018"

from ingest.template.spreadsheet_builder import SpreadsheetBuilder


# # build a generic spreadsheet from the latest schemas
# spreadsheet_builder = SpreadsheetBuilder("generic.xlsx")
# spreadsheet_builder.generate_workbook()
# spreadsheet_builder.save_workbook()
#
#
# # build a spreadsheet given new dev schemas
#
# dev_schemas = [
#     "http://schema.dev.data.humancellatlas.org/type/project/latest/project",
#     "http://schema.dev.data.humancellatlas.org/type/biomaterial/latest/cell_suspension",
#     "http://schema.dev.data.humancellatlas.org/type/biomaterial/latest/specimen_from_organism",
#     "http://schema.dev.data.humancellatlas.org/type/biomaterial/latest/donor_organism",
#     "http://schema.dev.data.humancellatlas.org/type/file/latest/sequence_file",
#     "http://schema.dev.data.humancellatlas.org/type/protocol/biomaterial_collection/latest/dissociation_protocol",
#     "http://schema.dev.data.humancellatlas.org/type/protocol/biomaterial_collection/latest/enrichment_protocol",
#     "http://schema.dev.data.humancellatlas.org/type/protocol/sequencing/latest/library_preparation_protocol",
#     "http://schema.dev.data.humancellatlas.org/type/protocol/sequencing/latest/sequencing_protocol",
# ]
#
# spreadsheet_builder = SpreadsheetBuilder("latest_dev_template.xlsx")
# spreadsheet_builder.generate_workbook(schema_urls=dev_schemas)
# spreadsheet_builder.save_workbook()
#
# # build a spreadsheet given a spreadsheet layout given a set of schemas
#
#
# dev_schemas.append("http://schema.dev.data.humancellatlas.org/type/process/latest/process")
#
# spreadsheet_builder = SpreadsheetBuilder("my_tabs_config.xlsx")
# spreadsheet_builder.generate_workbook(tabs_template="my_tabs_config.yaml", schema_urls=dev_schemas)
# spreadsheet_builder.save_workbook()


# build a generic spreadsheet from the latest schemas with a links config

biomaterial_links = {"specimen_from_organism": "donor_organism",
               "cell_suspension": "specimen_from_organism",
               "sequence_file": "cell_suspension"
               }

protocol_links = {
    "collection_protocol": [
      {
        "source": "donor_organism",
        "output": "specimen_from_organism"
      }
    ],
    "aggregate_generation_protocol": [
      {
        "source": "cell_line",
        "output": "organoid"
      },
      {
        "source": "specimen_from_organism",
        "output": "organoid"
      }
    ],
    "differentiation_protocol": [
      {
        "source": "cell_line",
        "output": "cell_suspension"
      },
      {
        "source": "cell_line",
        "output": "cell_line"
      },
      {
        "source": "cell_line",
        "output": "organoid"
      }
    ],
    "dissociation_protocol": [
       {
        "source": "specimen_from_organism",
        "output": "cell_line"
      },
      {
        "source": "specimen_from_organism",
        "output": "cell_suspension"
      },
      {
        "source": "cell_line",
        "output": "cell_suspension"
      },
       {
        "source": "organoid",
        "output": "cell_suspension"
      }
    ],
    "enrichment_protocol": [
      {
        "source": "specimen_from_organism",
        "output": "cell_line"
      },
      {
        "source": "specimen_from_organism",
        "output": "cell_suspension"
      },
      {
        "source": "cell_line",
        "output": "cell_suspension"
      },
      {
        "source": "organoid",
        "output": "cell_suspension"
      }
    ],
    "ipsc_induction_protocol": [
       {
        "source": "cell_line",
        "output": "cell_line"
      },
      {
        "source": "specimen_from_organism",
        "output": "cell_line"
      }
    ],
    "imaging_preparation_protocol": [
      {
        "source": "specimen_from_organism",
        "output": "imaged_specimen"
      }
    ],
    "imaging_protocol": [
      {
        "source": "imaged_specimen",
        "output": "image_file"
      }
    ],
    "library_preparation_protocol": [
      {
        "source": "cell_suspension",
        "output": "sequence_file"
      }
    ],
    "sequencing_protocol": [
      {
        "source": "cell_suspension",
        "output": "sequence_file"
      }
    ]
  }

spreadsheet_builder = SpreadsheetBuilder("generic.xlsx", biomaterial_links=biomaterial_links, protocol_links=protocol_links)
spreadsheet_builder.generate_workbook()
spreadsheet_builder.save_workbook()