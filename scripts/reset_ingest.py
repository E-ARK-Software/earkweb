import os
import sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
import shutil
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")


# Initialize Django (only needed if running standalone)
django.setup()

from django.core.exceptions import ObjectDoesNotExist
from earkweb.models import InformationPackage 

def reset_ingest():
    # Ask for the identifier
    identifier = input("Enter the identifier of the object to reset: ").strip()

    try:
        # Retrieve the InformationPackage object
        ip = InformationPackage.objects.get(identifier=identifier)

        # Confirm deletion
        confirm = input(f"Are you sure you want to reset the object '{identifier}'? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return

        # Delete the storage directory if it exists
        if ip.storage_dir and os.path.exists(ip.storage_dir):
            print(f"Deleting storage directory: {ip.storage_dir}")
            shutil.rmtree(ip.storage_dir)  # Recursively delete directory
        else:
            print("Storage directory does not exist or is already empty.")

        # Reset fields
        ip.storage_dir = ""
        ip.identifier = ""
        ip.version = 0

        # Save changes
        ip.save()
        print("Ingest reset successfully.")

    except ObjectDoesNotExist:
        print(f"No InformationPackage found with identifier: {identifier}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    reset_ingest()
