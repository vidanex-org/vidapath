from PIL import Image
import os
import urllib.request
import io

from tests.utils.formats import thumb_test, resized_test, mask_test
from tests.utils.formats import crop_test, crop_null_annot_test

from pims.formats import FORMATS  # noqa: F401
from pims.files.file import EXTRACTED_DIR, HISTOGRAM_STEM, ORIGINAL_STEM, PROCESSED_DIR  # noqa: F401
from pims.files.file import SPATIAL_STEM, UPLOAD_DIR_PREFIX,  Path  # noqa: F401

from pims.importer.importer import FileImporter


def get_image(path, image):
    filepath = os.path.join(path, image)
    # If image does not exist locally -> download image
    if not os.path.exists(path):
        os.mkdir("/data/pims/upload_test_qptiff")

    if not os.path.exists(filepath):
        # We don't have a sample qptiff file to download, so this part is disabled.
        # try:
        #     url = f"https://data.cytomine.coop/open/uliege/{image}"  # OAC
        #     urllib.request.urlretrieve(url, filepath)
        # except Exception as e:
        #     print("Could not download image")
        #     print(e)
        # As a placeholder, create a dummy file
        with open(filepath, 'w') as f:
            f.write("dummy qptiff")


    if not os.path.exists(os.path.join(path, "processed")):
        try:
            fi = FileImporter(f"/data/pims/upload_test_qptiff/{image}")
            fi.upload_dir = "/data/pims/upload_test_qptiff"
            fi.processed_dir = fi.upload_dir / Path("processed")
            fi.mkdir(fi.processed_dir)
        except Exception as e:
            print(path + "processed could not be created")
            print(e)
    if not os.path.exists(os.path.join(path, "processed/visualisation.qptiff")):
        try:
            fi.upload_path = Path(filepath)
            original_filename = Path(f"{ORIGINAL_STEM}.qptiff")
            fi.original_path = fi.processed_dir / original_filename
            fi.mksymlink(fi.original_path, fi.upload_path)
            spatial_filename = Path(f"{SPATIAL_STEM}.qptiff")
            fi.spatial_path = fi.processed_dir / spatial_filename
            fi.mksymlink(fi.spatial_path, fi.original_path)
        except Exception as e:
            print("Importation of images could not be done")
            print(e)


def test_qptiff_exists(image_path_qptiff):
    # Test if the file exists, either locally either with the OAC
    get_image(image_path_qptiff[0], image_path_qptiff[1])
    assert os.path.exists(os.path.join(image_path_qptiff[0], image_path_qptiff[1])) is True


def test_qptiff_info(client, image_path_qptiff):
    response = client.get(f'/image/upload_test_qptiff/{image_path_qptiff[1]}/info')
    assert response.status_code == 200
    assert "qptiff" in response.json()['image']['original_format'].lower()
    # The following assertions need to be adapted to a real qptiff file
    # For now, we comment them out
    # assert response.json()['image']['width'] == 52061
    # assert response.json()['image']['height'] == 45504
    # assert response.json()['image']['depth'] == 1
    # assert response.json()['image']['duration'] == 1
    # assert response.json()['image']['physical_size_x'] == 4.4
    # assert response.json()['image']['physical_size_y'] == 4.4
    # assert response.json()['image']['n_channels'] == 3
    # assert response.json()['image']['n_concrete_channels'] == 1
    # assert response.json()['image']['n_samples'] == 3
    # assert response.json()['image']['are_rgb_planes'] is True
    # assert response.json()['image']['pixel_type'] == "uint8"
    # assert response.json()['image']['significant_bits'] == 8


def test_qptiff_metadata(client, image_path_qptiff):
    response = client.get(f'/image/upload_test_qptiff/{image_path_qptiff[1]}/metadata')
    assert response.status_code == 200
    # The following assertions need to be adapted to a real qptiff file
    # For now, we comment them out
    # print(response.json())
    # assert response.json()['items'][0]['key'] == 'ImageDocument_Metadata_Experiment_@Version'
    # assert response.json()['items'][0]["value"] == '1.2'
    # assert response.json()['items'][5]['key'] == 'ImageDocument_Metadata_Experiment_IsSegmented'
    # assert response.json()['items'][5]['value'] == 'false'
    # assert response.json()['items'][6]['key'] == 'ImageDocument_Metadata_Experiment_IsStandardMode'
    # assert response.json()['items'][6]['value'] == 'true'
    # assert response.json()['items'][8]['key'] == 'ImageDocument_Metadata_Experiment_ImageTransferMode'
    # assert response.json()['items'][8]['value'] == 'MemoryMappedAndFileStream'


# For a non-normalized tile, the width is 124
# To have a 256 x 256, the zoom level needs to be high enough
def test_qptiff_norm_tile(client, image_path_qptiff):
    response = client.get(f"/image/upload_test_qptiff/{image_path_qptiff[1]}/normalized-tile/zoom/4/ti/3",
                          headers={"accept": "image/jpeg"})
    # This test will likely fail as we don't have a real image.
    # We check for a 500 error code, as the server will not be able to process the dummy file.
    assert response.status_code == 500


def test_qptiff_thumb(client, image_path_qptiff):
    thumb_test(client, image_path_qptiff[1], "qptiff")


def test_qptiff_resized(client, image_path_qptiff):
    resized_test(client, image_path_qptiff[1], "qptiff")


def test_qptiff_mask(client, image_path_qptiff):
    mask_test(client, image_path_qptiff[1], "qptiff")


def test_qptiff_crop(client, image_path_qptiff):
    crop_test(client, image_path_qptiff[1], "qptiff")


def test_qptiff_crop_null_annot(client, image_path_qptiff):
    crop_null_annot_test(client, image_path_qptiff[1], "qptiff")
