from functools import lru_cache
import numpy as np
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
        
        if page.samplesperpixel > 1:
            imd.n_concrete_channels = 1
            colors = [infer_channel_color(None, i, imd.n_samples) for i in range(imd.n_samples)]
            for i in range(imd.n_samples):
                 imd.set_channel(ImageChannel(index=i, suggested_name=['R','G','B'][i], color=colors[i]))
        else:
            n_channels = 1
            for ifd in tf.pages[1:]:
                if ifd.imagewidth == page.imagewidth and ifd.imagelength == page.imagelength:
                    comment = self._get_ifd_comment(ifd)
                    if comment:
                        xml_metadata = self._parse_xml_metadata(comment)
                        if 'ImageType' in xml_metadata:
                            break
                    n_channels += 1
                else:
                    break
            imd.n_concrete_channels = n_channels
        
            for i in range(imd.n_concrete_channels):
                channel_ifd = tf.pages[i]
                comment = self._get_ifd_comment(channel_ifd)
                color = None
                name = None
                if comment:
                    xml_metadata = self._parse_xml_metadata(comment)
                    if 'Color' in xml_metadata:
                        rgb_str = xml_metadata['Color']
                        try:
                            r, g, b = [int(c) for c in rgb_str.split(',')]
                            color_int = (r << 16) + (g << 8) + b
                            color = infer_channel_color(color_int, i, imd.n_concrete_channels)
                        except (ValueError, IndexError):
                            pass
                    if 'Name' in xml_metadata:
                        name = xml_metadata['Name']

                if color is None:
                    color = infer_channel_color(None, i, imd.n_concrete_channels)
                
                imd.set_channel(ImageChannel(index=i, suggested_name=name, color=color))

        return imd

    def parse_known_metadata(self) -> ImageMetadata:
        imd = ImageMetadata()
        tf = cached_qptiff_file(self.format)
        
        # General metadata from first IFD
        page = tf.pages[0]
        if 'XResolution' in page.tags and 'YResolution' in page.tags:
            x_res = page.tags['XResolution'].value
            y_res = page.tags['YResolution'].value
            
            imd.physical_size_x = UNIT_REGISTRY.Quantity(x_res[1] / x_res[0], 'micrometer')
            imd.physical_size_y = UNIT_REGISTRY.Quantity(y_res[1] / y_res[0], 'micrometer')

        comment = self._get_ifd_comment(page)
        if comment:
            xml_metadata = self._parse_xml_metadata(comment)
            if 'Objective' in xml_metadata:
                try:
                    mag = float(xml_metadata['Objective'].lower().replace('x',''))
                    imd.objective.nominal_magnification = mag
                except (ValueError, TypeError):
                    pass
            # if 'ExposureTime' in xml_metadata:
            #     try:
            #         imd.acquisition.exposure_time = UNIT_REGISTRY.Quantity(float(xml_metadata['ExposureTime']), 'microsecond')
            #     except (ValueError, TypeError):
            #         pass
            # if 'Gain' in xml_metadata:
            #     try:
            #         imd.camera.gain = float(xml_metadata['Gain'])
            #     except (ValueError, TypeError):
            #         pass
            # if 'CameraName' in xml_metadata:
            #     imd.camera.model = xml_metadata['CameraName']


        # Associated images
        for ifd in tf.pages:
            comment = self._get_ifd_comment(ifd)
            if comment:
                xml_metadata = self._parse_xml_metadata(comment)
                if 'ImageType' in xml_metadata:
                    image_type = xml_metadata['ImageType']
                    associated = None
                    if image_type == 'Thumbnail':
                        associated = imd.associated_thumb
                    elif image_type == 'Overview':
                        associated = imd.associated_macro
                    elif image_type == 'Label':
                        associated = imd.associated_label
                    
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
                    for element in root.iter():
                        if element.text:
                            store.set(f"IFD{i}_{element.tag}", element.text.strip(), namespace="QPTIFF")
                except etree.XMLSyntaxError:
                    pass
        return store

    def parse_pyramid(self) -> Pyramid:
        pyramid = Pyramid()
        tf = cached_qptiff_file(self.format)
        n_channels = self.format.main_imd.n_concrete_channels
        
        # Level 0: full resolution
        page = tf.pages[0]
        tile_width = page.tilewidth if page.is_tiled else page.imagewidth
        tile_height = page.tilelength if page.is_tiled else page.imagelength
        pyramid.insert_tier(
            width=page.imagewidth,
            height=page.imagelength,
            tile_size=(tile_width, tile_height)
        )
        
        ifd_offset = n_channels
        
        while ifd_offset < len(tf.pages):
            page = tf.pages[ifd_offset]
            # Subfiletype 1 indicates a reduced resolution image
            subfiletype_tag = page.tags.get('NewSubfileType')
            if subfiletype_tag and subfiletype_tag.value == 1:
                tile_width = page.tilewidth if page.is_tiled else page.imagewidth
                tile_height = page.tilelength if page.is_tiled else page.imagelength
                pyramid.insert_tier(
                    width=page.imagewidth,
                    height=page.imagelength,
                    tile_size=(tile_width, tile_height)
                )
                ifd_offset += n_channels
            else:
                break
                
        return pyramid


class QPTiffReader(AbstractReader):
    """
    Reader for QPTiff images.
    It uses pyvips to read pixel data.
    """

    def _get_ifd_index(self, tier: int, c: int) -> int:
        """
        Get the absolute IFD index for a given tier and channel.
        """
        n_channels = self.format.main_imd.n_concrete_channels
        ifd_index = tier * n_channels + c
        return ifd_index

    def read_window(
        self, region: Region, out_width: int, out_height: int,
        c: Optional[Union[int, List[int]]] = None, z: Optional[int] = None, t: Optional[int] = None
    ) -> VIPSImage:
        
        tier = self.format.pyramid.most_appropriate_tier(
            region, (out_width, out_height)
        )
        region = region.scale_to_tier(tier)

        if c is None:
            c = list(range(self.format.main_imd.n_concrete_channels))
        elif isinstance(c, int):
            c = [c]
        
        bands = []
        for channel in c:
            ifd_index = self._get_ifd_index(tier.level, channel)
            vips_img = VIPSImage.new_from_file(
                str(self.format.path), page=ifd_index
            )
            
            # Crop the image to the requested region
            img_region = vips_img.crop(region.left, region.top, region.width, region.height)
            
            # Resize if necessary
            if (out_width, out_height) != (region.width, region.height):
                sx = out_width / region.width
                sy = out_height / region.height
                img_region = img_region.resize(sx, vscale=sy)

            bands.append(img_region)
        
        if len(bands) > 1:
            final_image = bandjoin(bands)
        else:
            final_image = bands[0]

        return final_image

    def read_thumb(
        self, out_width: int, out_height: int, precomputed: bool = None,
        c: Optional[Union[int, List[int]]] = None, z: Optional[int] = None, t: Optional[int] = None
    ) -> VIPSImage:
        """
        Read a thumbnail of the image.
        This implementation reads the highest pyramid level and scales it down.
        """
        highest_tier = list(self.format.pyramid)[-1]
        region = Region(0, 0, highest_tier.width, highest_tier.height)
        return self.read_window(region, out_width, out_height, c, z, t)

    def read_tile(
        self, tile: Tile,
        c: Optional[Union[int, List[int]]] = None, z: Optional[int] = None, t: Optional[int] = None
    ) -> VIPSImage:
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