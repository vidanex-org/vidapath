import os
from functools import lru_cache
import numpy as np
import pyvips
from pyvips import Image as VIPSImage
from typing import Optional, Union, List
from lxml import etree
from tifffile import TiffFile
from datetime import datetime

from pims.utils import UNIT_REGISTRY
from pims.processing.region import Region, Tile
from pims.formats.utils.abstract import AbstractParser, AbstractReader, AbstractFormat, CachedDataPath
from pims.cache import cached_property
from pims.formats.utils.structures.metadata import ImageChannel, ImageMetadata, MetadataStore
from pims.formats.utils.structures.pyramid import Pyramid
from pims.formats.utils.engines.tifffile import TifffileChecker, cached_tifffile
from pims.formats.utils.histogram import DefaultHistogramReader
from pims.utils.color import infer_channel_color
from pims.utils.vips import bandjoin

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pims.format.qptiff")


class ExternalJPGLabel:
    """Helper for reading an external JPG label image."""
    def __init__(self, path):
        self.path = path
        try:
            with VIPSImage.new_from_file(self.path) as img:
                self._width = img.width
                self._height = img.height
        except Exception:
            # In case the file is corrupted or not an image
            self._width = 0
            self._height = 0

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def read(self):
        """Read the image and return it as a numpy array."""
        return VIPSImage.new_from_file(self.path)

    def __str__(self):
        return f"External JPEG Label ({self.width}x{self.height}) at {self.path}"


@lru_cache
def read_qptifffile(path):
    logger.debug(f"Read QPTiff file {path}")
    return TiffFile(str(path))

def cached_qptiff_file(format: AbstractFormat):
    return format.get_cached(
        '_qptiff', read_qptifffile, format.path.resolve()
    )


class QPTiffChecker(TifffileChecker):
    @classmethod
    def match(cls, pathlike: CachedDataPath) -> bool:
        tf = cached_tifffile(pathlike)
        page = tf.pages[0]
        software = page.tags.get('Software')
        if software:
            return software.value.startswith('PerkinElmer-QPI')
        return False


class QPTiffParser(AbstractParser):
    def _get_ifd_comment(self, ifd) -> Optional[str]:
        if 'ImageDescription' in ifd.tags:
            comment = ifd.tags['ImageDescription'].value
            if isinstance(comment, bytes):
                comment = comment.decode('utf-8')
            # The comment is XML, but it might have an incorrect encoding specified
            comment = comment.replace("utf-16", "utf-8")
            return comment
        return None

    def _parse_xml_metadata(self, xml_string: str) -> dict:
        if not xml_string:
            return {}

        def recurse_xml(element, path="", metadata=None):
            if metadata is None:
                metadata = {}
            
            key = f"{path}.{element.tag}" if path else element.tag

            if element.text and element.text.strip():
                metadata[key] = element.text.strip()

            for child in element:
                recurse_xml(child, path=key, metadata=metadata)
            
            return metadata

        try:
            root = etree.fromstring(xml_string.encode('utf-8'))
            return recurse_xml(root)
        except etree.XMLSyntaxError:
            logger.warning("Failed to parse QPTIFF XML metadata.")
            return {}

    def parse_main_metadata(self) -> ImageMetadata:
        tf = cached_qptiff_file(self.format)
        page = tf.pages[0]
        
        imd = ImageMetadata()
        imd.width = page.imagewidth
        imd.height = page.imagelength
        imd.pixel_type = page.dtype
        imd.n_samples = page.samplesperpixel
        
        # The root tag of the XML description
        root_key = 'PerkinElmer-QPI-ImageDescription'

        # Handle multi-channel grayscale images vs RGB images
        if page.samplesperpixel > 1:
            imd.n_concrete_channels = 1
            
            # For RGB, parse metadata from the first page's XML
            comment = self._get_ifd_comment(page)
            gain = None
            exposure_time = None
            if comment:
                xml_metadata = self._parse_xml_metadata(comment)
                gain_key_1 = f"{root_key}.CameraSettings.Gain"
                gain_key_2 = f"{root_key}.ScanProfile.root.CameraSettings.Gain"
                exposure_key = f"{root_key}.ExposureTime"

                if gain_key_1 in xml_metadata:
                    try: gain = float(xml_metadata[gain_key_1])
                    except (ValueError, TypeError): pass
                elif gain_key_2 in xml_metadata:
                    try: gain = float(xml_metadata[gain_key_2])
                    except (ValueError, TypeError): pass
                
                if exposure_key in xml_metadata:
                    try: exposure_time = UNIT_REGISTRY.Quantity(float(xml_metadata[exposure_key]), 'microsecond')
                    except (ValueError, TypeError): pass

            colors = [infer_channel_color(None, i, imd.n_samples) for i in range(imd.n_samples)]
            for i in range(imd.n_samples):
                ch = ImageChannel(index=i, suggested_name=['R','G','B'][i], color=colors[i])
                if gain is not None:
                    ch.gain = gain
                if exposure_time is not None:
                    ch.exposure_time = exposure_time
                imd.set_channel(ch)

        else:
            # Case 2: Multiple pages with 1 sample per pixel - multi-channel grayscale images
            # Let's identify which pages are actual channels by their characteristics
            actual_channels = []
            
            for idx, ifd in enumerate(tf.pages):
                comment = self._get_ifd_comment(ifd)
                if comment:
                    xml_metadata = self._parse_xml_metadata(comment)
                    image_type_key = f"{root_key}.ImageType"
                    if image_type_key in xml_metadata:
                        img_type = xml_metadata[image_type_key]
                        # Skip if this is a special image type (not a regular channel)
                        if img_type in ['Thumbnail', 'Label', 'Macro', 'Overview']:
                            continue
                
                # Check if this IFD has the same dimensions as the main page (indicating it's a channel)
                if ifd.imagewidth == page.imagewidth and ifd.imagelength == page.imagelength:
                    actual_channels.append(idx)
                else:
                    # Once we encounter a different sized image, we can stop checking
                    break
            
            # Limit to max 3 channels to prevent index out of bounds errors
            actual_channels = actual_channels[:3]
            # Set the concrete channel count to the number of actual channels found
            imd.n_concrete_channels = len(actual_channels)
            
            # Process each identified channel
            for i, channel_idx in enumerate(actual_channels):
                if channel_idx >= len(tf.pages):
                    continue
                channel_ifd = tf.pages[channel_idx]
                comment = self._get_ifd_comment(channel_ifd)
                
                color, name, biomarker, gain, exposure_time = None, None, None, None, None
                
                if comment:
                    xml_metadata = self._parse_xml_metadata(comment)
                    
                    # Define full keys
                    biomarker_key = f"{root_key}.Biomarker"
                    name_key = f"{root_key}.Name"
                    gain_key = f"{root_key}.CameraSettings.Gain"
                    exposure_key = f"{root_key}.ExposureTime"
                    color_key = f"{root_key}.Color"

                    if biomarker_key in xml_metadata and xml_metadata[biomarker_key]:
                        biomarker = xml_metadata[biomarker_key]
                        if name_key in xml_metadata and xml_metadata[name_key]:
                            name = xml_metadata[name_key]
                    elif name_key in xml_metadata and xml_metadata[name_key]:
                        name = xml_metadata[name_key]

                    gain_key_1 = f"{root_key}.CameraSettings.Gain"
                    gain_key_2 = f"{root_key}.ScanProfile.root.CameraSettings.Gain"
                    if gain_key_1 in xml_metadata:
                        try:
                            gain = float(xml_metadata[gain_key_1])
                        except (ValueError, TypeError): pass
                    elif gain_key_2 in xml_metadata:
                        try:
                            gain = float(xml_metadata[gain_key_2])
                        except (ValueError, TypeError): pass

                    if exposure_key in xml_metadata:
                        try:
                            exposure_time = UNIT_REGISTRY.Quantity(float(xml_metadata[exposure_key]), 'microsecond')
                        except (ValueError, TypeError): pass

                    if color_key in xml_metadata:
                        try:
                            r, g, b = [int(c) for c in xml_metadata[color_key].split(',')]
                            color = infer_channel_color((r, g, b), i, len(actual_channels))
                        except (ValueError, IndexError): pass

                if color is None:
                    final_name = biomarker if biomarker else name
                    if final_name:
                        fluor_map = {
                            'dapi': '#0000FF', 'fitc': '#00FF00', 'cy3': '#FF0000',
                            'cy5': '#FF00FF', 'texas red': '#FF0000'
                        }
                        mapped_color = fluor_map.get(str(final_name).lower())
                        if mapped_color:
                            color = infer_channel_color(mapped_color, i, len(actual_channels))

                if color is None:
                    color = infer_channel_color(None, i, len(actual_channels))
                
                if biomarker:
                    ch = ImageChannel(index=i, suggested_name=biomarker, color=color)
                    ch.fluor_name = name
                else:
                    ch = ImageChannel(index=i, suggested_name=name, color=color)
                
                if gain is not None:
                    ch.gain = gain
                if exposure_time is not None:
                    ch.exposure_time = exposure_time

                imd.set_channel(ch)

        return imd

    def parse_known_metadata(self) -> ImageMetadata:
        imd = ImageMetadata()
        tf = cached_qptiff_file(self.format)
        
        # General metadata from first IFD
        page = tf.pages[0]
        if 'XResolution' in page.tags and 'YResolution' in page.tags:
            # According to TIFF spec, 1=None, 2=Inch, 3=Centimeter
            resolution_unit_map = {2: 'inch', 3: 'cm'}
            unit = 'micrometer'  # Default unit if ResolutionUnit is not specified or is 1
            if 'ResolutionUnit' in page.tags:
                res_unit_val = page.tags['ResolutionUnit'].value
                unit = resolution_unit_map.get(res_unit_val, unit)

            x_res = page.tags['XResolution'].value
            y_res = page.tags['YResolution'].value

            # The value is pixels per resolution unit. We want unit per pixel.
            if hasattr(x_res, '__len__') and len(x_res) >= 2:
                size_x = x_res[1] / x_res[0]
                imd.physical_size_x = UNIT_REGISTRY.Quantity(size_x, unit).to('micrometer')
            elif isinstance(x_res, (int, float)) and x_res > 0:
                imd.physical_size_x = UNIT_REGISTRY.Quantity(1.0 / x_res, unit).to('micrometer')

            if hasattr(y_res, '__len__') and len(y_res) >= 2:
                size_y = y_res[1] / y_res[0]
                imd.physical_size_y = UNIT_REGISTRY.Quantity(size_y, unit).to('micrometer')
            elif isinstance(y_res, (int, float)) and y_res > 0:
                imd.physical_size_y = UNIT_REGISTRY.Quantity(1.0 / y_res, unit).to('micrometer')

        # Extract global metadata from XML
        comment = self._get_ifd_comment(page)
        if comment:
            xml_metadata = self._parse_xml_metadata(comment)
            root_key = 'PerkinElmer-QPI-ImageDescription'

            # Fallback for physical size from MsiResolution in XML
            key = f"{root_key}.ScanProfile.root.MsiResolution.PixelSizeMicrons"
            if imd.physical_size_x is None and key in xml_metadata:
                try:
                    size = float(xml_metadata[key])
                    # This value is already in microns, no conversion needed
                    imd.physical_size_x = UNIT_REGISTRY.Quantity(size, 'micrometer')
                    imd.physical_size_y = UNIT_REGISTRY.Quantity(size, 'micrometer') # Assume square pixels
                except (ValueError, TypeError):
                    logger.warning("Could not parse PixelSizeMicrons from XML.")

            key = f"{root_key}.Objective"
            if key in xml_metadata:
                try:
                    mag = float(xml_metadata[key].lower().replace('x',''))
                    imd.objective.nominal_magnification = mag
                except (ValueError, TypeError): pass
            
            key = f"{root_key}.OperatorName"
            if key in xml_metadata:
                imd.operator_name = xml_metadata[key]

            key = f"{root_key}.SampleDescription"
            if key in xml_metadata:
                imd.description = xml_metadata[key]

            key = f"{root_key}.AcquisitionSoftware"
            if key in xml_metadata:
                imd.microscope.model = xml_metadata[key]

        # Standard TIFF tags as fallbacks
        if 'DateTime' in page.tags:
            if not imd.acquisition_datetime:
                try:
                    dt_str = page.tags['DateTime'].value
                    imd.acquisition_datetime = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
                except (ValueError, TypeError):
                    logger.warning("Could not parse DateTime tag.")
        
        if 'Artist' in page.tags:
            if not imd.operator_name:
                imd.operator_name = page.tags['Artist'].value

        if 'Make' in page.tags:
            if not imd.microscope.manufacturer:
                imd.microscope.manufacturer = page.tags['Make'].value
        
        if 'Model' in page.tags:
            if not imd.microscope.model:
                imd.microscope.model = page.tags['Model'].value

        # Find and process associated images (thumbnail, label, macro)
        
        # Check for external label moved by the importer into the 'external-metadata' directory.
        # The format.path points to the file in the "processed" dir. We need to go up to the upload dir.
        try:
            upload_dir = self.format.path.parent.parent
            external_meta_dir = upload_dir / "external-metadata"
            label_path = external_meta_dir / "label.jpg"
            logger.info(f"Parser: Checking for moved external label at '{label_path}'")
            if label_path.exists():
                logger.info(f"Parser: Found external label at '{label_path}'. Loading it.")
                external_label = ExternalJPGLabel(label_path)
                imd.associated_label.width = external_label.width
                imd.associated_label.height = external_label.height
                imd.associated_label.page_index = -1 # Special index to signify external
                self.format._external_label = external_label # Cache for reader
            else:
                logger.info(f"Parser: No moved external label found at '{label_path}'.")
        except Exception as e:
            logger.warning(f"Parser: Error while checking for external metadata: {e}")

        for idx, ifd in enumerate(tf.pages):
            comment = self._get_ifd_comment(ifd)
            if comment:
                xml_metadata = self._parse_xml_metadata(comment)
                key = 'PerkinElmer-QPI-ImageDescription.ImageType'
                if key in xml_metadata:
                    image_type = xml_metadata[key]
                    associated = None
                    if image_type.lower() in ['thumbnail', 'thumb']:
                        associated = imd.associated_thumb
                    elif image_type.lower() == 'label' and not imd.associated_label.width:
                        # Only look for internal label if an external one was not found
                        associated = imd.associated_label
                    elif image_type.lower() in ['macro', 'overview']:
                        associated = imd.associated_macro
                    
                    if associated:
                        associated.width = ifd.imagewidth
                        associated.height = ifd.imagelength
                        associated.n_channels = ifd.samplesperpixel
                        associated.page_index = idx

        return imd

    def parse_raw_metadata(self) -> MetadataStore:
        store = MetadataStore()
        tf = cached_qptiff_file(self.format)

        def recurse_xml(element, path, store):
            # Construct the key path
            key = f"{path}.{element.tag}" if path else element.tag

            # If the element has text, store it.
            if element.text and element.text.strip():
                store.set(key, element.text.strip())

            # Recurse for children
            for child in element:
                recurse_xml(child, path=key, store=store)

        for i, ifd in enumerate(tf.pages):
            # Store PhotometricInterpretation if it exists
            if 'PhotometricInterpretation' in ifd.tags:
                try:
                    # The value is an enum member, so we get its name
                    value = ifd.tags['PhotometricInterpretation'].value.name
                    store.set(f"TIFF.IFD{i}.PhotometricInterpretation", value)
                except:
                    pass # Ignore if we cannot get the name

            comment = self._get_ifd_comment(ifd)
            if comment:
                try:
                    root = etree.fromstring(comment.encode('utf-8'))
                    recurse_xml(root, path=f"QPTIFF.IFD{i}", store=store)
                except etree.XMLSyntaxError:
                    # Fallback for non-XML or malformed comments
                    store.set(f"QPTIFF.IFD{i}.RawComment", comment)
        return store

    def parse_pyramid(self) -> Pyramid:
        pyramid = Pyramid()
        tf = cached_qptiff_file(self.format)
        main_imd = self.format.main_imd

        levels = {}  # (width, height) -> page_index

        # Find level 0
        levels[(main_imd.width, main_imd.height)] = 0

        # Find other pyramid levels by looking for reduced resolution pages
        for idx, page in enumerate(tf.pages):
            subfile_type = page.tags.get('NewSubfileType')
            # Check if it's a reduced resolution image (bit 0 of NewSubfileType is 1)
            if subfile_type and subfile_type.value & 1:
                dims = (page.imagewidth, page.imagelength)
                if dims not in levels:
                    # This is the first time we see this dimension, record its starting page index
                    levels[dims] = idx
        
        # Sort levels by width in descending order to build the pyramid from largest to smallest
        sorted_dims = sorted(levels.keys(), key=lambda d: d[0], reverse=True)
        
        for dims in sorted_dims:
            width, height = dims
            page_index = levels[dims]
            
            # Get tile size from the first page of the level
            page = tf.pages[page_index]
            tile_width = page.tilewidth if page.is_tiled else page.imagewidth
            tile_height = page.tilelength if page.is_tiled else page.imagelength
            
            pyramid.insert_tier(
                width=width,
                height=height,
                tile_size=(tile_width, tile_height),
                page_index=page_index
            )
            
        return pyramid


class QPTiffReader(AbstractReader):
    """
    Reader for QPTiff images.
    It uses pyvips to read pixel data.
    """
    def read_label(self, **kwargs) -> VIPSImage:
        """Read label image, whether it's internal or external."""
        if hasattr(self.format, '_external_label') and self.format._external_label:
            logger.info(f"Reading external label from: {self.format._external_label.path}")
            return self.format._external_label.read()
        
        # Fallback to internal label
        logger.info("Attempting to read internal label.")
        label_meta = self.format.parser.parse_known_metadata().associated_label
        if hasattr(label_meta, 'page_index') and label_meta.page_index != -1:
            logger.info(f"Found and reading internal label from page index {label_meta.page_index}")
            return VIPSImage.new_from_file(str(self.format.path), page=label_meta.page_index)
        
        logger.error("Could not find any internal or external label to read.")
        raise RuntimeError("No internal or external label found.")

    def _read_and_process_bands(
        self, page_indices: List[int], region: Region, out_width: int, out_height: int,
        scale_intensity: bool = False
    ) -> VIPSImage:
        """
        Core helper to read, join, and process image bands.
        Includes optional intensity scaling for thumbnail generation.
        """
        bands = []
        for page_index in page_indices:
            try:
                vips_img = VIPSImage.new_from_file(
                    str(self.format.path), page=page_index, access="sequential"
                )
                bands.append(vips_img)
            except pyvips.Error:
                logger.warning(f"Could not load page {page_index}. Skipping.")

        if not bands:
            raise RuntimeError(f"Could not read any bands for region {region}.")

        # Join bands into a single image
        image = bandjoin(bands) if len(bands) > 1 else bands[0]

        # Perform auto-scaling of intensity for grayscale-based images if requested
        if scale_intensity:
            # Only apply scaling to grayscale-based images, as RGB-like images may display correctly by default.
            if self.format.main_imd.n_samples == 1 and image.format != 'uchar':
                image = image.cast('float').scale().cast('uchar')
        
        # Crop the image to the requested region
        img_region = image.crop(region.left, region.top, region.width, region.height)
            
        # Resize if necessary
        if (out_width, out_height) != (region.width, region.height):
            sx = out_width / region.width
            sy = out_height / region.height
            img_region = img_region.resize(sx, vscale=sy)

        return img_region

    def read_window(
        self, region: Region, out_width: int, out_height: int,
        c: Optional[Union[int, List[int]]] = None, z: Optional[int] = None, t: Optional[int] = None,
        **kwargs
    ) -> VIPSImage:
        
        tier = self.format.pyramid.most_appropriate_tier(
            region, (out_width, out_height)
        )
        region = region.scale_to_tier(tier)
        page_start_index = tier.data['page_index']

        if c is None:
            c = list(range(self.format.main_imd.n_concrete_channels))
        elif isinstance(c, int):
            c = [c]
        
        page_indices = [page_start_index + channel for channel in c]
        
        # For read_window, return raw, unscaled data.
        return self._read_and_process_bands(
            page_indices, region, out_width, out_height, scale_intensity=False
        )

    def read_thumb(
        self, out_width: int, out_height: int, precomputed: bool = None,
        c: Optional[Union[int, List[int]]] = None, z: Optional[int] = None, t: Optional[int] = None,
        **kwargs
    ) -> VIPSImage:
        """
        Read a thumbnail of the image.
        Tries to use a precomputed thumbnail if available, otherwise generates
        it from the lowest-resolution pyramid level. Always scales intensity.
        """
        # 1. Try to read precomputed thumbnail by explicitly running the known metadata parser
        if precomputed is not False:
            # We run the parser to be sure associated images are populated.
            thumb_meta = self.format.parser.parse_known_metadata().associated_thumb
            if hasattr(thumb_meta, 'page_index'):
                region = Region(0, 0, thumb_meta.width, thumb_meta.height)
                return self._read_and_process_bands(
                    [thumb_meta.page_index], region, out_width, out_height, scale_intensity=True
                )

        if precomputed:
            raise ValueError("Precomputed thumbnail requested but not found.")

        # 2. Fallback to lowest-res pyramid level
        pyramid = self.format.pyramid
        if len(pyramid) > 0:
            lowest_tier = list(pyramid)[-1]
            region = Region(0, 0, lowest_tier.width, lowest_tier.height)
            
            # For thumbnails, use default channel 0 if not specified
            channels = c
            if channels is None:
                channels = [0]
            elif isinstance(channels, int):
                channels = [channels]

            page_start_index = lowest_tier.data['page_index']
            page_indices = [page_start_index + channel for channel in channels]
            
            return self._read_and_process_bands(
                page_indices, region, out_width, out_height, scale_intensity=True
            )

        raise RuntimeError("Could not generate thumbnail: no pyramid and no precomputed thumbnail found.")

    def read_tile(
        self, tile: Tile,
        c: Optional[Union[int, List[int]]] = None, z: Optional[int] = None, t: Optional[int] = None,
        **kwargs
    ) -> VIPSImage:
        # Tiles should return raw, unscaled data, like read_window.
        return self.read_window(tile, tile.width, tile.height, c, z, t)


class QPTiffFormat(AbstractFormat):
    checker_class = QPTiffChecker
    parser_class = QPTiffParser
    reader_class = QPTiffReader
    histogram_reader_class = DefaultHistogramReader

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enabled = True
        self._external_label = None

    @classmethod
    def get_name(cls) -> str:
        return "PerkinElmer Vectra QPTIFF"

    @classmethod
    def is_spatial(cls) -> bool:
        return True

    @cached_property
    def need_conversion(self) -> bool:
        return False
