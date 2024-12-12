import os
import uuid
import zipfile
import tarfile
from django.db import transaction
from earkweb.models import Representation

def register_representations_from_data_package(file_path, ip):
    """
    Process the container file to inspect its inventory and create Django representation objects.

    Args:
        file_path (str): Path to the container file (zip, tar, tar.gz).
        ip (object): The parent object for all representations.

    Raises:
        ValueError: If the container file format is unsupported or folder structure is invalid.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    root_folder = None
    representation_folders = []

    # Handle zip files
    if zipfile.is_zipfile(file_path):
        with zipfile.ZipFile(file_path, 'r') as zf:
            all_files = zf.namelist()
            root_folder = _extract_root_folder(all_files)
            representation_folders = _get_representation_folders(all_files, root_folder)

    # Handle tar or tar.gz files
    elif tarfile.is_tarfile(file_path):
        with tarfile.open(file_path, 'r:*') as tf:
            all_files = tf.getnames()
            root_folder = _extract_root_folder(all_files)
            representation_folders = _get_representation_folders(all_files, root_folder)

    else:
        raise ValueError("Unsupported file format. Only zip, tar, and tar.gz are supported.")

    if not root_folder:
        raise ValueError("No single root folder found in the container.")

    # Create Django objects for each representation folder
    representations = {}
    with transaction.atomic():
        for folder in representation_folders:
            representation_id = str(uuid.uuid4())
            # pylint: disable-next=no-member
            Representation.objects.create(
                ip=ip,
                identifier=representation_id,
                label=folder
            )
            representations[representation_id] = folder
    return representations


def _extract_root_folder(all_files):
    """
    Extract the single root folder from the file inventory.

    Args:
        all_files (list): List of file paths in the container.

    Returns:
        str: Name of the root folder, or None if invalid structure.
    """
    root_folders = {file.split('/')[0] for file in all_files if '/' in file}
    return root_folders.pop() if len(root_folders) == 1 else None

def _get_representation_folders(all_files, root_folder):
    """
    Get the folders under the 'representations' directory in the root folder.

    Args:
        all_files (list): List of file paths in the container.
        root_folder (str): The single root folder name.

    Returns:
        list: List of folder names under 'representations'.
    """
    representations_path = f"{root_folder}/representations"
    subfolders = set()

    for file in all_files:
        # Ensure the file path starts with the 'representations' path
        if file.startswith(f"{representations_path}/"):
            # Extract the portion after 'representations/' and split by '/'
            relative_path = file[len(representations_path) + 1:]
            parts = relative_path.split('/')
            if parts[0]:  # Ensure it's not empty
                subfolders.add(parts[0])

    return list(subfolders)
