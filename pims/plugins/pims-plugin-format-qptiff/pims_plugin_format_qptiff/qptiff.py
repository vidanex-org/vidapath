from functools import lru_cache
import numpy as np
import pyvips
from pyvips import Image as VIPSImage
from typing import Optional, Union, List
from lxml import etree
from tifffile import TiffFile

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
        try:
            root = etree.fromstring(xml_string.encode('utf-8'))
            metadata = {}
            for element in root.iter():
                if element.text:
                    metadata[element.tag] = element.text.strip()
            return metadata
        except etree.XMLSyntaxError:
            return {}

    def parse_main_metadata(self) -> ImageMetadata:
        tf = cached_qptiff_file(self.format)
        page = tf.pages[0]
        
        imd = ImageMetadata()
        imd.width = page.imagewidth
        imd.height = page.imagelength
        imd.pixel_type = page.dtype
        imd.n_samples = page.samplesperpixel
        
        # Handle multi-channel grayscale images vs RGB images
        if page.samplesperpixel > 1:
            imd.n_concrete_channels = 1
            colors = [infer_channel_color(None, i, imd.n_samples) for i in range(imd.n_samples)]
            for i in range(imd.n_samples):
                 imd.set_channel(ImageChannel(index=i, suggested_name=['R','G','B'][i], color=colors[i]))

        else:
            # Case 2: Multiple pages with 1 sample per pixel - multi-channel grayscale images
            # Let's identify which pages are actual channels by their characteristics
            actual_channels = []
            
            for idx, ifd in enumerate(tf.pages):
                comment = self._get_ifd_comment(ifd)
                if comment:
                    xml_metadata = self._parse_xml_metadata(comment)
                    if 'ImageType' in xml_metadata:
                        img_type = xml_metadata['ImageType']
                        # Skip if this is a special image type (not a regular channel)
                        if img_type in ['Thumbnail', 'Label', 'Macro', 'Overview']:
                            continue
                
                # Check if this IFD has the same dimensions as the main page (indicating it's a channel)
                if ifd.imagewidth == page.imagewidth and ifd.imagelength == page.imagelength:
                    # Additional check: if this page has samplesperpixel > 1, it might be a multichannel RGB page
                    # But since we're in the else branch, the first page had samplesperpixel = 1
                    actual_channels.append(idx)
                else:
                    # Once we encounter a different sized image, we can stop checking
                    # since pyramid levels and other images typically come after all channels
                    break
            
            # Limit to max 3 channels to prevent index out of bounds errors
            actual_channels = actual_channels[:3]
            # Set the concrete channel count to the number of actual channels found
            imd.n_concrete_channels = len(actual_channels)
            
            # Process each identified channel
            for i, channel_idx in enumerate(actual_channels):
                # Get the current IFD
                if channel_idx >= len(tf.pages):
                    continue  # Skip if index is out of bounds
                channel_ifd = tf.pages[channel_idx]
                
                # Get comment for this channel
                comment = self._get_ifd_comment(channel_ifd)
                
                color = None
                name = None
                biomarker = None
                
                if comment:
                    xml_metadata = self._parse_xml_metadata(comment)
                    if 'Biomarker' in xml_metadata and xml_metadata['Biomarker']:
                        biomarker = xml_metadata['Biomarker']
                        if 'Name' in xml_metadata and xml_metadata['Name']:
                            name = xml_metadata['Name']
                    elif 'Name' in xml_metadata and xml_metadata['Name']:
                        name = xml_metadata['Name']

                    # Priority 1: Use the <Color> tag from the file's metadata if it exists.
                    if 'Color' in xml_metadata:
                        rgb_str = xml_metadata['Color']
                        try:
                            r, g, b = [int(c) for c in rgb_str.split(',')]
                            # Pass the tuple directly, as infer_channel_color can handle it.
                            # This avoids incorrect integer conversion.
                            color = infer_channel_color((r, g, b), i, len(actual_channels))
                        except (ValueError, IndexError):
                            pass

                # Priority 2: If no color from XML, try to infer from channel name
                if color is None:
                    final_name = biomarker if biomarker else name
                    if final_name:
                        fluor_map = {
                            'dapi': '#0000FF',
                            'fitc': '#00FF00', # Pure Green
                            'cy3': '#FF0000',
                            'cy5': '#FF00FF', # Magenta
                            'texas red': '#FF0000'
                        }
                        mapped_color = fluor_map.get(final_name.lower())
                        if mapped_color:
                            color = infer_channel_color(mapped_color, i, len(actual_channels))

                # Priority 3: Final fallback to index-based color
                if color is None:
                    color = infer_channel_color(None, i, len(actual_channels))
                
                # Create channel with appropriate name
                if biomarker:
                    ch = ImageChannel(index=i, suggested_name=biomarker, color=color)
                    ch.fluor_name = name
                else:
                    ch = ImageChannel(index=i, suggested_name=name, color=color)
                
                imd.set_channel(ch)

        return imd

    def parse_known_metadata(self) -> ImageMetadata:
        imd = ImageMetadata()
        tf = cached_qptiff_file(self.format)
        
        # General metadata from first IFD
        page = tf.pages[0]
        if 'XResolution' in page.tags and 'YResolution' in page.tags:
            x_res = page.tags['XResolution'].value
            y_res = page.tags['YResolution'].value
            
            # Calculate physical sizes (tifffile stores as rationals)
            if hasattr(x_res, '__len__') and len(x_res) >= 2:
                imd.physical_size_x = UNIT_REGISTRY.Quantity(x_res[1] / x_res[0], 'micrometer')
            elif isinstance(x_res, (int, float)):
                imd.physical_size_x = UNIT_REGISTRY.Quantity(1.0 / x_res, 'micrometer') if x_res != 0 else None
                
            if hasattr(y_res, '__len__') and len(y_res) >= 2:
                imd.physical_size_y = UNIT_REGISTRY.Quantity(y_res[1] / y_res[0], 'micrometer')
            elif isinstance(y_res, (int, float)):
                imd.physical_size_y = UNIT_REGISTRY.Quantity(1.0 / y_res, 'micrometer') if y_res != 0 else None

        # Extract metadata from first channel's XML
        comment = self._get_ifd_comment(page)
        if comment:
            # Use a simple parsing for known, top-level metadata.
            # More complex parsing is done in parse_raw_metadata.
            xml_metadata = self._parse_xml_metadata(comment)
            if 'Objective' in xml_metadata:
                try:
                    mag = float(xml_metadata['Objective'].lower().replace('x',''))
                    imd.objective.nominal_magnification = mag
                except (ValueError, TypeError):
                    pass
            if 'ExposureTime' in xml_metadata:
                try:
                    imd.exposure_time = UNIT_REGISTRY.Quantity(float(xml_metadata['ExposureTime']), 'microsecond')
                except (ValueError, TypeError):
                    pass
            if 'OperatorName' in xml_metadata:
                imd.operator_name = xml_metadata['OperatorName']
            if 'SampleDescription' in xml_metadata:
                imd.description = xml_metadata['SampleDescription']
            if 'AcquisitionSoftware' in xml_metadata:
                imd.microscope.model = xml_metadata['AcquisitionSoftware']

        # Find and process associated images (thumbnail, label, macro)
        for idx, ifd in enumerate(tf.pages):
            comment = self._get_ifd_comment(ifd)
            if comment:
                xml_metadata = self._parse_xml_metadata(comment)
                if 'ImageType' in xml_metadata:
                    image_type = xml_metadata['ImageType']
                    associated = None
                    if image_type.lower() in ['thumbnail', 'thumb']:
                        associated = imd.associated_thumb
                    elif image_type.lower() == 'label':
                        associated = imd.associated_label
                    elif image_type.lower() in ['macro', 'overview']:
                        associated = imd.associated_macro
                    
                    if associated:
                        associated.width = ifd.imagewidth
                        associated.height = ifd.imagelength
                        associated.n_channels = ifd.samplesperpixel

        return imd

    def parse_raw_metadata(self) -> MetadataStore:
        store = MetadataStore()
        tf = cached_qptiff_file(self.format)
        for i, ifd in enumerate(tf.pages):
            comment = self._get_ifd_comment(ifd)
            if comment:
                try:
                    root = etree.fromstring(comment.encode('utf-8'))
                    for element in root:
                        tag = element.tag
                        value = element.text.strip() if element.text else None
                        
                        # Store top-level simple elements
                        if value:
                            store.set(f"QPTIFF.IFD{i}.{tag}", value)

                        # Store children of complex elements (like CameraSettings)
                        for child in element:
                            child_tag = child.tag
                            child_value = child.text.strip() if child.text else None
                            if child_value:
                                store.set(f"QPTIFF.IFD{i}.{tag}.{child_tag}", child_value)

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
        # 1. Try to read precomputed thumbnail
        if precomputed is not False:
            thumb_meta = self.format.parser.parse_known_metadata().associated_thumb
            if thumb_meta and thumb_meta.width and thumb_meta.height:
                tf = cached_qptiff_file(self.format)
                for idx, page in enumerate(tf.pages):
                    comment = self.format.parser._get_ifd_comment(page)
                    if comment:
                        xml_metadata = self.format.parser._parse_xml_metadata(comment)
                        image_type = xml_metadata.get('ImageType', '').lower()
                        if image_type in ['thumbnail', 'thumb']:
                            region = Region(0, 0, thumb_meta.width, thumb_meta.height)
                            return self._read_and_process_bands(
                                [idx], region, out_width, out_height, scale_intensity=True
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

    @classmethod
    def get_name(cls) -> str:
        return "PerkinElmer Vectra QPTIFF"

    @classmethod
    def is_spatial(cls) -> bool:
        return True

    @cached_property
    def need_conversion(self) -> bool:
        return False
