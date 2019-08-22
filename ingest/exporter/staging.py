import logging

from ingest.exporter.metadata import MetadataResource
from ingest.exporter.exceptions import FileDuplication

from ingest.api.ingestapi import IngestApi
from ingest.api.stagingapi import StagingApi

logger = logging.getLogger(__name__)


class StagingInfo:

    def __init__(self, staging_area_uuid: str, file_name: str, metadata_uuid: str, cloud_url: str):
        self.staging_area_uuid = staging_area_uuid
        self.file_name = file_name
        self.metadata_uuid = metadata_uuid
        self.cloud_url = cloud_url


class StagePersistInfo:

    def __init__(self, staging_area_uuid: str, file_name: str):
        self.staging_area_uuid = staging_area_uuid
        self.file_name = file_name


class StagingInfoRepository:
    def __init__(self, ingest_client: IngestApi):
        self.ingest_client = ingest_client

    def delete_staging_locks(self, staging_area_uuid: str):
        self.ingest_client.delete_staging_jobs(staging_area_uuid)

    def save(self, stage_persist_info: StagePersistInfo):
        pass


class StagingService:

    def __init__(self, staging_client: StagingApi, staging_info_repository: StagingInfoRepository):
        self.staging_client = staging_client
        self.staging_info_repository = staging_info_repository

    def staging_area_exists(self, staging_area_uuid: str) -> bool:
        return self.staging_client.hasStagingArea(staging_area_uuid)

    def get_staging_info(self, staging_area_uuid, metadata_resource: MetadataResource):
        file_name = metadata_resource.get_staging_file_name()
        staging_info = self.staging_info_repository.find_one(staging_area_uuid, file_name)
        if not staging_info.cloud_url:
            file_description = self.staging_client.getFile(staging_area_uuid, file_name)
            staging_info.cloud_url = file_description.url
            self.staging_info_repository.update(staging_info)
        return staging_info

    def stage_metadata(self, staging_area_uuid, metadata_resource: MetadataResource) -> StagingInfo:
        staging_file_name = metadata_resource.get_staging_file_name()

        try:
            self.staging_info_repository.save(StagePersistInfo(staging_area_uuid, staging_file_name))
            formatted_type = f'metadata/{metadata_resource.metadata_type}'
            file_description = self.staging_client.stageFile(staging_area_uuid, staging_file_name,
                                                             metadata_resource.to_bundle_metadata(),
                                                             formatted_type)
        except FileDuplication as file_duplication:
            logger.warning(str(file_duplication))
            file_description = self.staging_client.getFile(staging_area_uuid, staging_file_name)

        staging_info = StagingInfo(staging_area_uuid, staging_file_name, metadata_resource.uuid, file_description.url)
        return staging_info

    def cleanup_staging_area(self, staging_area_uuid):
        self.staging_client.deleteStagingArea(staging_area_uuid)
        self.staging_info_repository.delete_staging_locks(staging_area_uuid)
