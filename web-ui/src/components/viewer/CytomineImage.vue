<!-- Copyright (c) 2009-2022. Authors: see NOTICE file.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.-->

<template>
  <div class="map-container" @click="isActiveImage = true" ref="container">
    <div class="map-container-header">
      <a @click="$emit('close')" class="close">
        <i class="fa fa-times" aria-hidden="true"></i>
      </a>
    </div>
    <template v-if="!loading && zoom !== null">
      <div class="map-tools">
        <ul class="map-tools-list">
          <li><a title="Zoom in" @click="zoomIn()"><i class="fas fa-search-plus fa-fw"></i></a></li>
          <li><a title="Zoom out" @click="zoomOut()"><i class="fas fa-search-minus fa-fw"></i></a></li>
          <li v-if="isPanelDisplayed('digital-zoom')">
            <a @click="togglePanel('digital-zoom')" :class="{ active: activePanel === 'digital-zoom' }">
              <i class="fas fa-search fa-fw"></i>
            </a>
            <digital-zoom class="panel-options" v-show="activePanel === 'digital-zoom'" :index="index"
              @resetZoom="$refs.view.animate({ zoom: image.zoom })" @fitZoom="fitZoom" />
          </li>
          <li>
            <a title="Rotate" @click="togglePanel('rotation')" :class="{ active: activePanel === 'rotation' }">
              <i class="fa fa-undo fa-fw" aria-hidden="true"></i>
            </a>
            <rotation-selector class="panel-options" v-show="activePanel === 'rotation'" :index="index" />
          </li>
          <hr class="is-divider">
          <!-- AI Analysis Panel Button -->
          <li>
            <a title="AI Analysis" @click="toggleAIAnalysisPanel" :class="{ active: showAIAnalysisPanel }">
              <i class="fas fa-robot fa-fw"></i>
            </a>
          </li>
          <li>
            <a title="Pathology Report" @click="toggleReportDrawer" :class="{ active: showReportDrawer }">
              <i class="fas fa-file-medical fa-fw"></i>
            </a>
          </li>
          <hr class="is-divider" />
          <li>
            <a @click="togglePanel('layers')" :class="{ active: activePanel === 'layers' }">
              <i class="fas fa-copy fa-fw"></i>
            </a>
            <layers-panel class="panel-options" v-show="activePanel === 'layers'" :index="index" />
          </li>
          <li v-if="isPanelDisplayed('color-manipulation')">
            <a @click="togglePanel('colors')" :class="{ active: activePanel === 'colors' }">
              <i class="fas fa-adjust fa-fw"></i>
            </a>
            <color-manipulation class="panel-options" v-show="activePanel === 'colors'" :index="index" />
          </li>
          <hr class="is-divider" />
          <li v-if="isPanelDisplayed('info')">
            <a @click="togglePanel('info')" :class="{ active: ['info', 'metadata'].includes(activePanel) }">
              <i class="fas fa-info fa-fw"></i>
            </a>
            <information-panel class="panel-options" v-show="activePanel === 'info'" :index="index" />
          </li>
          <li v-if="configUI['project-tools-screenshot']">
            <a @click="takeScreenshot()" :class="{ active: activePanel === 'screenshot' }">
              <i class="fas fa-camera fa-fw"></i>
            </a>
          </li>
          <li>
            <a @click="toggleFullscreen">
              <i :class="isFullscreen ? 'fas fa-compress fa-fw' : 'fas fa-expand fa-fw'"></i>
            </a>
          </li>
          <li v-if="!$keycloak.hasTemporaryToken">
            <a @click="ShareByLink()">
              <i class="fa fa-share-alt fa-fw" aria-hidden="true"></i>
            </a>
          </li>
        </ul>
      </div>
      <vl-map :data-projection="projectionName" :load-tiles-while-animating="true" :load-tiles-while-interacting="true"
        :keyboard-event-target="document" @pointermove="projectedMousePosition = $event.coordinate"
        @mounted="updateKeyboardInteractions" ref="map">
        <vl-view :center.sync="center" :zoom.sync="zoom" :rotation.sync="rotation" :max-zoom="maxZoom"
          :max-resolution="Math.pow(2, image.zoom)" :extent="extent" :projection="projectionName"
          @mounted="viewMounted()" ref="view" />
        <vl-layer-tile :extent="extent" @mounted="addOverviewMap" ref="baseLayer">
          <vl-source-cytomine :projection="projectionName" :url="baseLayerURL" :tile-load-function="tileLoadFunction"
            :size="imageSize" :extent="extent" :nb-resolutions="image.zoom" ref="baseSource" @mounted="setBaseSource()"
            :transition="0" :tile-size="[tileSize, tileSize]" />
        </vl-layer-tile>
        <annotation-layer v-for="layer in selectedLayers" :key="'layer-' + layer.id" :index="index" :layer="layer" />
        <select-interaction v-if="activeSelectInteraction" :index="index" />
        <draw-interaction v-if="activeDrawInteraction" :index="index" />
        <modify-interaction v-if="activeModifyInteraction" :index="index" />
      </vl-map>
      <div v-if="configUI['project-tools-main']" class="draw-tools">
        <draw-tools :index="index" @screenshot="takeScreenshot()" />
      </div>
      <scale-line v-show="scaleLineCollapsed" :image="image" :zoom="zoom" :mousePosition="projectedMousePosition" />
      <magnification-selector v-if="image.magnification" :image="image" :zoom="zoom"
        @setMagnification="setMagnification" @fit="fitZoom" />
      <toggle-scale-line :index="index" />
      <annotations-container :index="index" @centerView="centerViewOnAnnot" />
      <div class="custom-overview" ref="overview">
        <p class="image-name" :class="{ hidden: overviewCollapsed }">
          <image-name :image="image" />
        </p>
      </div>

      <!-- AI Analysis Panel -->
      <div v-if="showAIAnalysisPanel" class="ai-analysis-panel">
        <pathology-viewer :project="project" :index="index" />
      </div>

      <!-- Share Project Modal -->
      <share-project-modal :active="shareModalActive" :project="project" @update:active="shareModalActive = $event" />

      <!-- Add Ontology Modal -->
      <add-ontology-modal :active="showAddOntologyModal" :index="index" @close="showAddOntologyModal = false" />

      <!-- Pathology Report Drawer -->
      <pathology-report-drawer :active="showReportDrawer" @close="showReportDrawer = false" />
    </template>
  </div>
</template>
<script>
import { get } from '@/utils/store-helpers';
import _ from 'lodash';
import ImageName from '@/components/image/ImageName';
import AnnotationLayer from './AnnotationLayer';
import ScaleLine from './ScaleLine';
import MagnificationSelector from './MagnificationSelector';
import SelectInteraction from './interactions/SelectInteraction';
import DrawInteraction from './interactions/DrawInteraction';
import ModifyInteraction from './interactions/ModifyInteraction';
import ToggleScaleLine from './interactions/ToggleScaleLine';
import { addProj, createProj, getProj } from 'vuelayers/lib/ol-ext';
import View from 'ol/View';
import OverviewMap from 'ol/control/OverviewMap';
import { KeyboardPan, KeyboardZoom } from 'ol/interaction';
import { noModifierKeys, targetNotEditable } from 'ol/events/condition';
import WKT from 'ol/format/WKT';
import { Cytomine, ImageConsultation, Annotation, UserPosition, SliceInstance } from '@/api';
// import {constLib, operation} from '@/utils/color-manipulation.js';
import constants from '@/utils/constants.js';
export default {
  name: 'cytomine-image',
  props: {
    index: String
  },
  components: {
    ImageName,
    AnnotationLayer,
    ScaleLine,
    MagnificationSelector,
    SelectInteraction,
    DrawInteraction,
    ModifyInteraction,
    ToggleScaleLine,
    // 异步加载非核心组件，加快首屏渲染速度
    RotationSelector: () => import('./RotationSelector'),
    DrawTools: () => import('./DrawTools'),
    AnnotationsContainer: () => import('./AnnotationsContainer'),
    InformationPanel: () => import('./panels/InformationPanel'),
    DigitalZoom: () => import('./panels/DigitalZoom'),
    ColorManipulation: () => import('./panels/ColorManipulation'),
    LayersPanel: () => import('./panels/LayersPanel'),
    PathologyViewer: () => import('./PathologyViewer.vue'),
    ShareProjectModal: () => import('@/components/project/ShareProjectModal.vue'),
    PathologyReportDrawer: () => import('./PathologyReportDrawer.vue'),
    AddOntologyModal: () => import('./panels/AddOntologyModal.vue')
  },
  data() {
    return {
      minZoom: 0,
      projectedMousePosition: [0, 0],
      baseSource: null,
      routedAnnotation: null,
      selectedAnnotation: null,
      timeoutSavePosition: null,
      loading: true,
      overview: null,
      format: new WKT(),
      isFullscreen: false,
      // AI Analysis Panel
      showAIAnalysisPanel: false,
      // Pathology Report Drawer
      showReportDrawer: false,
      showAddOntologyModal: false,
      // Share Modal
      shareModalActive: false,
      layers: [], // Array<User> (representing user layers)
    };
  },
  computed: {
    shortTermToken: get('currentUser/shortTermToken'),
    document() {
      return document;
    },
    project: get('currentProject/project'),
    routedAction() {
      return this.$route.query.action;
    },
    configUI: get('currentProject/configUI'),
    viewerModule() {
      return this.$store.getters['currentProject/currentViewerModule'];
    },
    imageModule() {
      return this.$store.getters['currentProject/imageModule'](this.index);
    },
    viewerWrapper() {
      return this.$store.getters['currentProject/currentViewer'];
    },
    nbImages() {
      return Object.keys(this.viewerWrapper.images).length;
    },
    imageWrapper() {
      return this.viewerWrapper.images[this.index];
    },
    image() {
      return this.imageWrapper.imageInstance;
    },
    slices() {
      return this.imageWrapper.activeSlices;
    },
    sliceIds() {
      return this.slices.map(slice => slice.id);
    },
    canEdit() {
      return this.$store.getters['currentProject/canEditImage'](this.image);
    },
    projectionName() {
      return `CYTO-${this.image.id}`;
    },
    selectedLayers() {
      return this.imageWrapper.layers.selectedLayers || [];
    },
    isActiveImage: {
      get() {
        return this.viewerWrapper.activeImage === this.index;
      },
      set(value) {
        if (value) {
          if (this.viewerWrapper) {
            this.$store.commit(this.viewerModule + 'setActiveImage', this.index);
          }
        } else {
          throw new Error('Cannot unset active map');
        }
      }
    },
    activePanel() {
      return this.imageWrapper.activePanel;
    },
    activeTool() {
      return this.imageWrapper.draw.activeTool;
    },
    activeEditTool() {
      return this.imageWrapper.draw.activeEditTool;
    },
    maxZoom() {
      return this.$store.getters[this.imageModule + 'maxZoom'];
    },
    center: {
      get() {
        return this.imageWrapper.view.center;
      },
      set(value) {
        this.$store.dispatch(this.viewerModule + 'setCenter', { index: this.index, center: value });
      }
    },
    zoom: {
      get() {
        return this.imageWrapper.view.zoom;
      },
      set(value) {
        this.$store.dispatch(this.viewerModule + 'setZoom', { index: this.index, zoom: Number(value) });
      }
    },
    rotation: {
      get() {
        return this.imageWrapper.view.rotation;
      },
      set(value) {
        this.$store.dispatch(this.viewerModule + 'setRotation', { index: this.index, rotation: Number(value) });
      }
    },
    viewState() {
      return { center: this.center, zoom: this.zoom, rotation: this.rotation };
    },
    extent() {
      return [0, 0, this.image.width, this.image.height];
    },
    imageSize() {
      return [this.image.width, this.image.height];
    },
    tileSize() {
      return this.image.tileSize;
    },
    baseLayerProcessingParams() {
      return this.$store.getters[this.imageModule + 'tileRequestParams'];
    },
    baseLayerSliceParams() {
      return {
        zSlices: this.slices[0].zStack,
        timepoints: this.slices[0].time
      };
    },
    baseLayerURLQuery() {
      let query = new URLSearchParams({ ...this.baseLayerSliceParams, ...this.baseLayerProcessingParams }).toString();
      if (query.length > 0) {
        return `?${query}`;
      }
      return query;
    },
    baseLayerURL() {
      let slice = this.slices[0];
      return Cytomine.instance.host + Cytomine.instance.basePath + `sliceinstance/${slice.id}/normalized-tile/zoom/{z}/tx/{x}/ty/{y}.jpg${this.baseLayerURLQuery}`;
    },
    tileLoadFunction() {
      return (tile, src) => {
        const xhr = new XMLHttpRequest();
        xhr.responseType = 'blob';
        // 检查是否为临时访问令牌用户
        if (this.$keycloak && this.$keycloak.hasTemporaryToken) {
          // 从URL中提取access_token并添加到请求URL中
          const urlParams = new URLSearchParams(window.location.hash.split('?')[1] || '');
          const accessToken = urlParams.get('access_token');
          if (accessToken) {
            const separator = src.includes('?') ? '&' : '?';
            const urlWithToken = `${src}${separator}access_token=${accessToken}`;
            xhr.open('GET', urlWithToken);
          } else {
            xhr.open('GET', src);
          }
        } else {
          // 正常用户使用shortTermToken
          xhr.open('GET', src);
          xhr.setRequestHeader('Authorization', 'Bearer ' + this.shortTermToken);
        }
        xhr.addEventListener('load', () => {
          const url = URL.createObjectURL(xhr.response);
          const tileImage = tile.getImage();
          tileImage.addEventListener('load', () => URL.revokeObjectURL(url));
          tileImage.src = url;
        });
        xhr.send();
      };
    },
    overviewCollapsed() {
      return this.overview ? this.overview.getCollapsed() : this.imageWrapper.view.overviewCollapsed;
    },
    scaleLineCollapsed() {
      return !this.imageWrapper.view.scaleLineCollapsed;
    },
    correction() {
      return ['correct-add', 'correct-remove'].includes(this.activeEditTool);
    },
    activeSelectInteraction() {
      return this.activeTool === 'select';
    },
    activeDrawInteraction() {
      return !this.activeSelectInteraction || this.correction;
    },
    activeModifyInteraction() {
      return this.activeSelectInteraction && this.activeEditTool && !this.correction;
    },
    idealZoom() {
      let container = this.$refs.container;
      let idealZoom = this.maxZoom;
      let factor = this.maxZoom - this.image.zoom;
      let mapWidth = this.image.width * Math.pow(2, factor);
      let mapHeight = this.image.height * Math.pow(2, factor);
      while (mapWidth > container.clientWidth || mapHeight > container.clientHeight) {
        mapWidth /= 2;
        mapHeight /= 2;
        idealZoom--;
      }
      return idealZoom;
    }
  },
  watch: {
    viewState() {
      this.savePosition();
    },
    overviewCollapsed(value) {
      this.$store.commit(this.imageModule + 'setOverviewCollapsed', value);
    }
  },
  methods: {
    rotate() {
      //TODO
    },
    zoomIn() {
      this.$refs.view.animate({ zoom: this.zoom + 1, duration: 250 });
    },
    zoomOut() {
      this.$refs.view.animate({ zoom: this.zoom - 1, duration: 250 });
    },
    setMagnification(mag) {
      if (!this.image || !this.image.magnification) return;
      let targetZoom = this.image.zoom + Math.log2(mag / this.image.magnification);
      this.$refs.view.animate({ zoom: targetZoom, duration: 500 });
    },
    activatePan() {
      this.$store.dispatch(this.imageModule + 'draw/activateTool', 'pan');
    },
    setInitialZoom() {
      if (this.zoom !== null) {
        return; // not the first time the viewer is opened => zoom was already initialized
      }
      this.zoom = this.idealZoom;
    },
    toggleAIAnalysisPanel() {
      this.showAIAnalysisPanel = !this.showAIAnalysisPanel;
    },
    toggleReportDrawer() {
      this.showReportDrawer = !this.showReportDrawer;
    },
    ShareByLink() {
      this.shareModalActive = true;
    },
    async updateMapSize() {
      await this.$nextTick();
      if (this.$refs.map) {
        this.$refs.map.updateSize();
      }
    },
    async updateKeyboardInteractions() {
      await this.$refs.map.$createPromise; // wait for ol.Map to be created
      this.$refs.map.$map.getInteractions().forEach(interaction => {
        if (interaction instanceof KeyboardPan || interaction instanceof KeyboardZoom) {
          interaction.condition_ = (mapBrowserEvent) => {
            return noModifierKeys(mapBrowserEvent)
              && targetNotEditable(mapBrowserEvent)
              && this.isActiveImage
              && !mapBrowserEvent.originalEvent.target.classList.contains('ql-editor');
          };
        }
      });
    },
    async viewMounted() {
      await this.$refs.view.$createPromise; // wait for ol.View to be created
      if (this.routedAnnotation) {
        this.centerViewOnAnnot(this.routedAnnotation, 500);
      }
      this.savePosition();
    },
    async setBaseSource() {
      await this.$refs.baseSource.$createPromise;
      this.baseSource = this.$refs.baseSource.$source;
    },
    async addOverviewMap() {
      if (!this.isPanelDisplayed('overview')) {
        return;
      }
      await this.$refs.map.$createPromise; // wait for ol.Map to be created
      await this.$refs.baseLayer.$createPromise; // wait for ol.Layer to be created
      let map = this.$refs.map.$map;
      this.overview = new OverviewMap({
        view: new View({ projection: this.projectionName }),
        layers: [this.$refs.baseLayer.$layer],
        tipLabel: this.$t('overview'),
        target: this.$refs.overview,
        collapsed: this.imageWrapper.view.overviewCollapsed
      });
      map.addControl(this.overview);
      this.overview.getOverviewMap().on(('click'), (evt) => {
        let size = map.getSize();
        map.getView().centerOn(evt.coordinate, size, [size[0] / 2, size[1] / 2]);
      });
    },
    toggleOverview() {
      if (this.overview) {
        this.overview.setCollapsed(!this.imageWrapper.view.overviewCollapsed);
      }
    },
    togglePanel(panel) {
      this.$store.commit(this.imageModule + 'togglePanel', panel);
    },
    savePosition: _.debounce(async function () {
      if (this.$refs.view) {
        let extent = this.$refs.view.$view.calculateExtent(); // [minX, minY, maxX, maxY]
        try {
          await UserPosition.create({
            image: this.image.id,
            slice: this.slices[0].id,
            zoom: this.zoom,
            rotation: this.rotation,
            bottomLeftX: Math.round(extent[0]),
            bottomLeftY: Math.round(extent[1]),
            bottomRightX: Math.round(extent[2]),
            bottomRightY: Math.round(extent[1]),
            topLeftX: Math.round(extent[0]),
            topLeftY: Math.round(extent[3]),
            topRightX: Math.round(extent[2]),
            topRightY: Math.round(extent[3]),
            broadcast: this.imageWrapper.tracking.broadcast
          });
        } catch (error) {
          console.log(error);
          this.$notify({ type: 'error', text: this.$t('notif-error-save-user-position') });
        }
        clearTimeout(this.timeoutSavePosition);
        this.timeoutSavePosition = setTimeout(this.savePosition, constants.SAVE_POSITION_IN_IMAGE_INTERVAL);
      }
    }, 500),
    fitZoom() {
      this.$refs.view.animate({
        zoom: this.idealZoom,
        center: [this.image.width / 2, this.image.height / 2]
      });
    },
    async centerViewOnAnnot(annot, duration) {
      if (annot.image === this.image.id) {
        if (!annot.location) {
          //in case annotation location has not been loaded
          annot = (await Cytomine.instance.api.get(`/annotations/${annot.id}`)).data;
          if (Object.prototype.hasOwnProperty.call(annot, 'annotationLayer')) {
            annot.location = decodeURIComponent(atob(annot.location));
          }
        }
        if (annot.project !== this.project.id) {
          await this.$router.push(`/project/${annot.project}/image/${annot.image}/annotation/${annot.id}`);
        }
        let geometry = this.format.readGeometry(annot.location);
        await this.$refs.view.fit(geometry, { duration, padding: [10, 10, 10, 10], maxZoom: this.image.zoom });
        if (!Object.prototype.hasOwnProperty.call(annot, 'centroid')) {
          return;
        }
        // HACK: center set by view.fit() is incorrect => reset it manually
        this.center = (geometry.getType() === 'Point') ? geometry.getFirstCoordinate()
          : [annot.centroid.x, annot.centroid.y];
        // ---
      }
    },
    async selectAnnotationHandler({ index, annot, center = false, showComments = false }) {
      if (this.index === index && annot.image === this.image.id) {
        try {
          let sliceChange = false;
          if (!annot.slice) {
            //in case annotation slice has not been loaded
            annot = await Annotation.fetch(annot.id);
          }
          if (!this.sliceIds.includes(annot.slice)) {
            let slice = await SliceInstance.fetch(annot.slice);
            await this.$store.dispatch(this.imageModule + 'setActiveSlice', slice);
            this.$eventBus.$emit('reloadAnnotations', { idImage: this.image.id, hard: true });
            sliceChange = true;
          }
          if (showComments) {
            this.$store.commit(this.imageModule + 'setShowComments', annot);
          }
          this.selectedAnnotation = annot; // used to pre-load annot layer
          this.$store.commit(this.imageModule + 'setAnnotToSelect', annot);
          this.$eventBus.$emit('selectAnnotationInLayer', { index, annot });
          if (center) {
            await this.viewMounted();
            let duration = (sliceChange) ? undefined : 500;
            this.centerViewOnAnnot(annot, duration);
          }
        } catch (error) {
          console.log(error);
          this.$notify({ type: 'error', text: this.$t('notif-error-target-annotation') });
        }
      }
    },
    isPanelDisplayed(panel) {
      return this.configUI[`project-explore-${panel}`];
    },
    shortkeyHandler(key) {
      if (!key.startsWith('toggle-all-') && !this.isActiveImage) { // shortkey should only be applied to active map
        return;
      }
      key = key.replace('toggle-all-', 'toggle-');
      switch (key) {
        case 'toggle-information':
          if (this.isPanelDisplayed('info')) {
            this.togglePanel('info');
          }
          return;
        case 'toggle-zoom':
          if (this.isPanelDisplayed('digital-zoom')) {
            this.togglePanel('digital-zoom');
          }
          return;
        case 'toggle-link':
          if (this.isPanelDisplayed('link') && this.nbImages > 1) {
            this.togglePanel('link');
          }
          return;
        case 'toggle-filters':
          if (this.isPanelDisplayed('color-manipulation')) {
            this.togglePanel('colors');
          }
          return;
        case 'toggle-layers':
          if (this.isPanelDisplayed('image-layers')) {
            this.togglePanel('layers');
          }
          return;
        case 'toggle-ontology':
          if (this.isPanelDisplayed('ontology')) {
            this.togglePanel('ontology');
          }
          return;
        case 'toggle-annotations-list':
          if (this.isPanelDisplayed('annotations-list')) {
            this.togglePanel('annotations-list');
          }
          return;
        case 'toggle-properties':
          if (this.isPanelDisplayed('property')) {
            this.togglePanel('properties');
          }
          return;
        case 'toggle-broadcast':
          if (this.isPanelDisplayed('follow')) {
            this.togglePanel('follow');
          }
          return;
        case 'toggle-review':
          if (this.isPanelDisplayed('review') && this.canEdit) {
            this.togglePanel('review');
          }
          return;
        case 'toggle-overview':
          if (this.isPanelDisplayed('overview')) {
            this.toggleOverview();
          }
          return;
      }
    },
    async takeScreenshot() {
      // Use of css percent values and html2canvas results in strange behavior
      // Set image container as actual height in pixel (not in percent) to avoid image distortion when retrieving canvas
      let containerHeight = document.querySelector('.map-container').clientHeight;
      document.querySelector('.map-container').style.height = containerHeight + 'px';
      let a = document.createElement('a');
      a.href = await this.$html2canvas(document.querySelector('.ol-unselectable'), { type: 'dataURL' });
      let imageName = 'image_' + this.image.id.toString() + '_project_' + this.image.project.toString() + '.png';
      a.download = imageName;
      a.click();
      // Reset container css values as previous
      document.querySelector('.map-container').style.height = '';
    },
    toggleFullscreen() {
      const element = this.$el;
      if (!document.fullscreenElement &&
        !document.webkitFullscreenElement &&
        !document.mozFullScreenElement &&
        !document.msFullscreenElement) {
        // 进入全屏
        if (element.requestFullscreen) {
          element.requestFullscreen();
        } else if (element.webkitRequestFullscreen) {
          element.webkitRequestFullscreen();
        } else if (element.mozRequestFullScreen) {
          element.mozRequestFullScreen();
        } else if (element.msRequestFullscreen) {
          element.msRequestFullscreen();
        }
      } else {
        // 退出全屏
        if (document.exitFullscreen) {
          document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
          document.webkitExitFullscreen();
        } else if (document.mozCancelFullScreen) {
          document.mozCancelFullScreen();
        } else if (document.msExitFullscreen) {
          document.msExitFullscreen();
        }
      }
    },
    handleFullscreenChange() {
      this.isFullscreen = !!(document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.mozFullScreenElement ||
        document.msFullscreenElement);
    },

    async fetchLayers() {
      this.layers = (await this.project.fetchUserLayers(this.image.id)).array;

      let layers = (await Cytomine.instance.api.get(`image-instances/${this.image.id}/annotation-layers`)).data;
      this.layers.push(...layers);

      // if image instance was changed (e.g. with previous/next image navigation), some of the selected layers
      // may not be relevant for the current image => filter them
      let idLayers = this.layers.map(layer => layer.id);
      this.$store.commit(this.imageModule + 'filterSelectedLayers', idLayers);
    },
  },
  async created() {
    if (!getProj(this.projectionName)) { // if image opened for the first time
      let projection = createProj({ code: this.projectionName, units: 'pixels', extent: this.extent });
      addProj(projection);
    }
    if (this.routedAction === 'review') {
      this.togglePanel('review');
      if (!this.image.inReview) {
        try {
          let clone = await this.image.clone().review();
          this.$store.commit(this.imageModule + 'setImageInstance', clone);
        } catch (error) {
          console.log(error);
          this.$notify({ type: 'error', text: this.$t('notif-error-start-review') });
        }
      }
      this.$store.commit(this.imageModule + 'setReviewMode', true);
    }
    // remove all selected features in order to reselect them when they will be added to the map (otherwise,
    // issue with the select interaction)
    this.selectedLayers.forEach(layer => {
      this.$store.commit(this.imageModule + 'removeLayerFromSelectedFeatures', { layer, cache: true });
    });
    let annot = this.imageWrapper.routedAnnotation;
    if (!annot) {
      let idRoutedAnnot = this.$route.params.idAnnotation;
      if (idRoutedAnnot) {
        try {
          annot = (await Cytomine.instance.api.get(`/annotations/${idRoutedAnnot}`)).data;
          if (Object.prototype.hasOwnProperty.call(annot, 'annotationLayer')) {
            annot.location = decodeURIComponent(atob(annot.location));
          }
        } catch (error) {
          console.log(error);
          this.$notify({ type: 'error', text: this.$t('notif-error-target-annotation') });
        }
      }
    }
    if (annot) {
      if (Object.prototype.hasOwnProperty.call(annot, 'annotationLayer')) {
        let response = await Cytomine.instance.api.get(`/annotation-layers/${annot.annotationLayer}/task-run-layer`);
        let taskRunLayer = response.data;
        annot.image = taskRunLayer.image;
      }
      try {
        if (annot.image === this.image.id) {
          if (!this.sliceIds.includes(annot.slice) && Object.prototype.hasOwnProperty.call(annot, 'slice')) {
            let slice = await SliceInstance.fetch(annot.slice);
            await this.$store.dispatch(this.imageModule + 'setActiveSlice', slice);
          }
          this.routedAnnotation = annot;
          if (this.routedAction === 'comments') {
            this.$store.commit(this.imageModule + 'setShowComments', annot);
          }
          this.$store.commit(this.imageModule + 'setAnnotToSelect', annot);
        }
        this.$store.commit(this.imageModule + 'clearRoutedAnnotation');
      } catch (error) {
        console.log(error);
        this.$notify({ type: 'error', text: this.$t('notif-error-target-annotation') });
      }
    }
    // 不阻塞初始化流程，异步保存浏览记录
    new ImageConsultation({ image: this.image.id }).save().catch(error => {
      console.log(error);
      // 这种非关键性错误可以不打扰用户，或者保留通知
      // this.$notify({ type: 'error', text: this.$t('notif-error-save-image-consultation') });
    });

    // 异步加载图层，不阻塞界面渲染
    this.fetchLayers().catch(error => {
      console.log(error);
      this.$notify({ type: 'error', text: this.$t('notif-error-loading-annotation-layers') });
    });
    this.loading = false;
  },
  mounted() {
    this.$eventBus.$on('updateMapSize', this.updateMapSize);
    this.$eventBus.$on('shortkeyEvent', this.shortkeyHandler);
    this.$eventBus.$on('selectAnnotation', this.selectAnnotationHandler);
    this.$eventBus.$on('close-metadata', () => this.$store.commit(this.imageModule + 'togglePanel', 'info'));
    this.$eventBus.$on('openAddOntologyModal', () => this.showAddOntologyModal = true);
    this.setInitialZoom();
    // 添加全屏事件监听器
    document.addEventListener('fullscreenchange', this.handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', this.handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', this.handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', this.handleFullscreenChange);
  },
  beforeDestroy() {
    this.$eventBus.$off('updateMapSize', this.updateMapSize);
    this.$eventBus.$off('shortkeyEvent', this.shortkeyHandler);
    this.$eventBus.$off('selectAnnotation', this.selectAnnotationHandler);
    this.$eventBus.$off('close-metadata');
    this.$eventBus.$off('openAddOntologyModal');
    clearTimeout(this.timeoutSavePosition);
    // 移除全屏事件监听器
    document.removeEventListener('fullscreenchange', this.handleFullscreenChange);
    document.removeEventListener('webkitfullscreenchange', this.handleFullscreenChange);
    document.removeEventListener('mozfullscreenchange', this.handleFullscreenChange);
    document.removeEventListener('MSFullscreenChange', this.handleFullscreenChange);
  }
};
</script>
<style lang="scss">
@import '~vuelayers/lib/style.css';
@import '../../assets/styles/colors';
@import '../../assets/styles/dark-variables';
$widthPanelBar: 2.8rem;
// Map to global variables
$backgroundPanelBar: $dark-wapper-bg;
$colorPanelLink: $dark-text-secondary;
$colorHoverPanelLink: $dark-text-primary;
$colorBorderPanelLink: $dark-border-color;
$colorOpenedPanelLink: $primary;

.ai-analysis-panel {
  position: absolute;
  top: 60px;
  left: 60px;
  z-index: 100;
  // background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  max-width: 400px;
  max-height: 80vh;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .ai-analysis-panel {
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    max-width: 90vw;
  }
}

/* Mobile adaptation for AI Panel */
@media (max-width: 768px) {
  .ai-analysis-panel {
    top: auto !important;
    bottom: 0 !important;
    left: 0 !important;
    transform: none !important;
    width: 100% !important;
    max-width: 100% !important;
    max-height: 70vh;
    border-radius: 12px 12px 0 0;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.2);
  }
}

.map-container {
  display: flex;
  background-color: $dark-wapper-bg;
  width: 100%;
  height: 100%;
}

.map-container-header {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 30;

  .close {
    color: $dark-text-secondary;
    font-size: 1.5rem;

    :hover {
      color: $dark-text-primary;
    }
  }
}

.draw-tools {
  position: absolute;
  top: 0.7em;
  left: 3.5rem;
  right: $widthPanelBar;
  z-index: 30;
}

@media (max-width: 768px) {
  .draw-tools {
    left: 10px;
    right: 10px;
    overflow-x: auto;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
    /* Hide scrollbar for cleaner look */
    scrollbar-width: none; 
    &::-webkit-scrollbar {
      display: none;
    }
  }
}

.broadcast {
  position: absolute;
  right: 4.5rem;
  top: 0.7em;
  text-transform: uppercase;
  font-weight: 600;
  background-color: #EE4242;
  color: white;
  padding: 0.25em 0.75em 0.25em 0.55em;
  border-radius: 5px;
  border: 2px solid white;

  i.fas {
    margin-right: 0.3em;
  }
}

.panel-options {
  position: absolute;
  bottom: -1.75em;
  left: $widthPanelBar;
  width: 24em;
  // min-height: 5em;
  background: rgba($dark-bg-primary, 0.9);
  color: $dark-text-primary;
  padding: 0.75em;
  border-radius: 5px;
  z-index: 100;

  h1 {
    font-size: 1.5rem;
    padding-top: 0.3rem !important;
    padding-bottom: 1rem !important;
    background: $dark-bg-primary;
    color: $dark-text-primary;
  }

  table {
    background: none;
    width: 100%;
    background: $dark-bg-primary;
    color: $dark-text-primary;
  }
}

/* Mobile adaptation for Side Panels (Bottom Sheet style) */
@media (max-width: 768px) {
  .panel-options {
    position: fixed; /* Break out of the relative parent */
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    width: 100% !important;
    max-height: 60vh;
    overflow-y: auto;
    border-radius: 12px 12px 0 0;
    box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.3);
    z-index: 1000; /* Ensure it's on top */
  }
}

.annotations-list-panel-container {
  position: absolute;
  top: -30vh;
  left: 60px;
  background: $dark-bg-primary;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  max-height: 80vh;
  overflow-y: auto;
  z-index: 100;
}

/* Responsive styles for annotations list panel */
@media (max-width: 768px) {
  .annotations-list-panel-container {
    // top: 50%;
    // left: 50%;
    transform: translate(-50%, -50%);
    max-width: 90vw;
  }
}

/* ----- Metadata panel ---- */
.panel-metadata {
  position: absolute;
  top: -1.5em;
  right: $widthPanelBar;
  min-width: 30em;
  min-height: 30em;
  background: $backgroundPanelBar;
  padding: 0.75em;
  border-radius: 5px 0 0 5px;
}

/* ----- CUSTOM STYLE FOR OL CONTROLS ----- */
.ol-zoom {
  display: none;
}

.ol-rotate {
  background: none !important;
  z-index: 20;
  // display: none;
}

.ol-control button {
  background: white !important;
  color: black !important;
  border-radius: 2px !important;
  box-shadow: 0 0 1px #777;

  &:hover {
    box-shadow: 0 0 1px black;
    cursor: pointer;
  }
}

.ol-zoom-in {
  margin-bottom: 5px !important;
}

.custom-overview {
  position: absolute;
  bottom: 0.5em;
  left: 4em;
  background: rgba($dark-bg-secondary, 0.8);
  display: flex;
  flex-direction: column;
  border-radius: 4px;

  .ol-overviewmap {
    position: static;
    background: none;
  }

  .ol-overviewmap:not(.ol-collapsed) button {
    bottom: 2px !important;
  }

  .image-name {
    font-size: 0.8em;
    padding: 2px 5px;
    width: 158px;
    word-wrap: break-word;

    &.hidden {
      display: none;
    }
  }
}

@media (max-width: 768px) {
  .custom-overview {
    display: none; /* Hide overview on mobile */
  }
}

/* ----- Image controls ----- */
.image-controls-wrapper {
  position: absolute;
  bottom: 1.5rem;
  left: 20%;
  right: calc(#{$widthPanelBar} + 20%);
  z-index: 5;
}

/* ----- Annotation list ----- */
.annotations-table-wrapper {
  position: absolute;
  bottom: 0;
  left: 0;
  right: $widthPanelBar;
  z-index: 40;
  pointer-events: none;
}

.map-tools {
  background: $backgroundPanelBar;
  display: flex;
  font-size: 0.9em;
  border-left: 1px solid $colorBorderPanelLink;

  >ul {
    padding: 0;
    margin: 0;

    >li {
      position: relative;

      >a {
        position: relative;
        display: block;
        font-size: 1.5rem;
        color: $colorPanelLink;
        text-decoration: none;
        text-align: center;

        &:hover {
          color: $colorHoverPanelLink;
        }

        &.active {
          background: $dark-bg-secondary;
          color: $colorOpenedPanelLink;
        }
      }
    }
  }
}

.map-tools-list {
  padding: 0;
  margin: 0;
  list-style: none;
}

.map-tools-list>li {
  position: relative;
}

.map-tools-list>li>a {
  position: relative;
  display: block;
  width: $widthPanelBar;
  padding: 0.35rem 0.8rem;
  font-size: 1.25rem;
  color: $colorPanelLink;
  text-decoration: none;
  text-align: center;
  cursor: pointer;
}

.map-tools-list>li>a:hover {
  color: $colorHoverPanelLink;
}
</style>
