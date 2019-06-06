#!/usr/bin/env python

"""
python list_bundles.py --project-uuid=b6dc9b93-929a-45d0-beb2-5cf8e64872fe --env=prod
"""

import json
import logging
import sys
from optparse import OptionParser

from ingest.api.ingestapi import IngestApi


class BundleTracker:
    def __init__(self, ingest_api):
        self.ingest_api = ingest_api

    def get_bundles(self, project_uuid):
        project = self.ingest_api.get_project_by_uuid(project_uuid)
        submissions = self.ingest_api.get_related_entities("submissionEnvelopes", project,
                                              "submissionEnvelopes")
        for submission in submissions:
            bundle_manifests = self.ingest_api.get_related_entities("bundleManifests", submission,
                                                       "bundleManifests")
            for bundle_manifest in bundle_manifests:
                yield bundle_manifest

    def generate_bundle_fqids(self, project_uuid):
        bundle_fqids = []
        for bundle in self.get_bundles(project_uuid):
            uuid = bundle.get('bundleUuid')
            version = bundle.get('bundleVersion')
            fqid = f'{uuid}{version}'
            bundle_fqids.append(fqid)
        return bundle_fqids


if __name__ == '__main__':
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=format, stream=sys.stdout, level=logging.INFO)

    parser = OptionParser()
    parser.add_option("-p", "--project-uuid", help="Project UUID")
    parser.add_option("-e", "--env", help="Project UUID")
    parser.add_option("-o", "--output-file", help="Output filename")
    (options, args) = parser.parse_args()

    if not options.project_uuid:
        print("Please supply a project-uuid and env")
        exit(2)

    if not options.env:
        print("Please supply which environment this script should run")
        exit(2)

    filename = options.output_file or f'{options.project_uuid}.json'

    infix = f'.{options.env}' if options.env != 'prod' else ''
    url = f'https://api.ingest{infix}.data.humancellatlas.org'
    ingest_api = IngestApi(url)
    bundle_tracker = BundleTracker(ingest_api=ingest_api)

    fqids = bundle_tracker.generate_bundle_fqids(options.project_uuid)

    with open(filename, 'w') as outfile:
        json.dump(fqids, outfile, indent=4)

    print(f'Total bundle count: {len(fqids)}')
    print(f'Saved into file:{filename}')
