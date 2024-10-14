import os
import uuid

from rest_framework import serializers
from earkweb.models import InformationPackage, InternalIdentifier, UploadedFile
from config.configuration import config_path_work

import logging

logger = logging.getLogger(__name__)


class InformationPackageSerializer(serializers.Serializer):
    uid = serializers.CharField(required=False, allow_blank=True, max_length=255, help_text="UUID of the information package")
    work_dir = serializers.CharField(required=False, allow_blank=True, max_length=4096, help_text="Path to the working copy of the information package")
    package_name = serializers.CharField(required=False, allow_blank=True, max_length=255, help_text="Name of the information package")
    external_id = serializers.CharField(required=False, allow_blank=True, max_length=255, help_text="Name of the information package")
    identifier = serializers.CharField(required=False, allow_blank=True, max_length=255, help_text="Local identifier of the data set")
    version = serializers.IntegerField(required=False, help_text="Version of the data set")
    storage_dir = serializers.CharField(required=False, allow_blank=True, max_length=4096, help_text="Storage location of the data set")
    basic_metadata = serializers.CharField(required=False, allow_blank=True, max_length=4096, help_text="Basic metadata in JSON format")
    last_change = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        """
        Create and return a new `InformationPackage` instance, given the validated data.
        """
        if 'version' not in validated_data:
            validated_data['version'] = -1
        if 'external_id' not in validated_data:
            validated_data['external_id'] = "example:undefined"
        if 'uid' not in validated_data:
            uid = str(uuid.uuid4())
            validated_data['uid'] = uid
            validated_data['work_dir'] = os.path.join(config_path_work, uid)
        if 'user_id' not in validated_data:
            validated_data['user_id'] = self.context['request'].user.id
        if 'basic_metadata' not in validated_data:
            validated_data['basic_metadata'] = "{}"
        return InformationPackage.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `InformationPackage` instance, given the validated data.
        """
        instance.uid = validated_data.get('uid', instance.uid)
        instance.work_dir = validated_data.get('work_dir', instance.work_dir)
        instance.package_name = validated_data.get('package_name', instance.package_name)
        instance.identifier = validated_data.get('identifier', instance.identifier)
        instance.version = validated_data.get('version', instance.version)
        instance.storage_dir = validated_data.get('storage_dir', instance.storage_dir)
        instance.last_change = validated_data.get('last_change', instance.last_change)
        instance.basic_metadata = validated_data.get('basic_metadata', instance.basic_metadata)
        instance.save()
        return instance


class InternalIdentifierSerializer(serializers.Serializer):
    org_nsid = serializers.CharField(required=False, allow_blank=True, max_length=200)
    identifier = serializers.CharField(required=False, allow_blank=True, max_length=200)
    created = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        """
        Create and return a new `information package` instance, given the validated data.
        """
        return InternalIdentifier.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Snippet` instance, given the validated data.
        """
        instance.package_name = validated_data.get('package_name', instance.package_name)
        instance.org_nsid = validated_data.get('org_nsid', instance.org_nsid)
        instance.save()
        return instance

    class Meta:
        model = InternalIdentifier
        fields = ('identifier', 'org_nsid')

class UploadedFileSerializer(serializers.HyperlinkedModelSerializer):
    file = serializers.HyperlinkedRelatedField(
        many=True, read_only=True,
        view_name='uploadedfile-detail'
        )
    class Meta:
        model = UploadedFile
        fields = ('url', 'creator','creation_datetime','title','file')

