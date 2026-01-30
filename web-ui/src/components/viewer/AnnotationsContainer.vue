<template>
  <div>
    <annotation-details-container 
      class="annotations-container"
      :index="index" 
      @select="selectAnnotation"
      @centerView="centerView({ annot: $event, sameView: true })" 
      @addTerm="addTerm"
       @addTrack="addTrack"
      @updateTermsOrTracks="updateTermsOrTracks" 
      @updateProperties="updateProperties" 
      @delete="handleDeletion" />

     <annotations-list
      class="annotations-table-wrapper"
      :index="index"
      @select="selectAnnotation"
      @centerView="centerView"
      @addTerm="addTerm"
      @addTrack="addTrack"
      @updateTermsOrTracks="updateTermsOrTracks"
      @updateProperties="updateProperties"
      @delete="handleDeletion"
    />
  </div>
</template>

<script>
import { get } from '@/utils/store-helpers';
import { Action, updateTermProperties, updateTrackProperties } from '@/utils/annotation-utils.js';

import WKT from 'ol/format/WKT';

import AnnotationsList from './AnnotationsList';
import AnnotationDetailsContainer from './AnnotationDetailsContainer';
import { listAnnotationsInGroup, updateAnnotationLinkProperties } from '@/utils/annotation-utils';

import { Annotation } from '@/api';

export default {
  name: 'AnnotationsContainer',
  props: {
    index: String,
  },
  data() {
    return {
      format: new WKT(),
    };
  },
  components: {
    AnnotationsList,
    AnnotationDetailsContainer,
  },
  computed: {
    configUI: get('currentProject/configUI'),
    viewerModule() {
      return this.$store.getters['currentProject/currentViewerModule'];
    },
    viewerWrapper() {
      return this.$store.getters['currentProject/currentViewer'];
    },
    imageModule() {
      return this.$store.getters['currentProject/imageModule'](this.index);
    },
    imageWrapper() {
      return this.$store.getters['currentProject/currentViewer'].images[this.index];
    },
    image() {
      return this.imageWrapper.imageInstance;
    },
    imageGroupId() {
      return this.$store.getters[this.imageModule + 'imageGroupId'];
    },
    copiedAnnot: {
      get() {
        return this.viewerWrapper.copiedAnnot;
      },
      set(annot) {
        this.$store.commit(this.viewerModule + 'setCopiedAnnot', annot);
      }
    },
    showSimilarAnnotations() {
      return this.imageWrapper.selectedFeatures.showSimilarAnnotations;
    },
  },
  methods: {
    isPanelDisplayed(panel) {
      return this.configUI[`project-explore-${panel}`];
    },

    addTerm(term) {
      this.$store.dispatch(this.viewerModule + 'addTerm', term);
    },

    addTrack(track) {
      this.$store.dispatch(this.viewerModule + 'refreshTracks', { idImage: track.image });
    },

    async updateTermsOrTracks(annot) {
      let updatedAnnot = await annot.clone().fetch();
      updatedAnnot.imageGroup = this.imageGroupId;
      await updateTermProperties(updatedAnnot);
      await updateTrackProperties(updatedAnnot);
      await updateAnnotationLinkProperties(updatedAnnot);

      this.$eventBus.$emit('editAnnotation', updatedAnnot);
      this.$store.commit(this.imageModule + 'changeAnnotSelectedFeature', { indexFeature: 0, annot: updatedAnnot });
    },

    updateProperties() {
      this.$store.dispatch(this.imageModule + 'refreshProperties', this.index);
    },

    async handleDeletion(annot) {
      this.$store.commit(this.imageModule + 'addAction', { annot: annot, type: Action.DELETE });

      if (annot.group) {
        let editedAnnots = [];
        if (annot.annotationLink.length === 2) {
          // If there were 2 links, the group has been deleted by backend
          let otherId = annot.annotationLink.filter(al => al.annotation !== annot.id)[0].annotation;
          let other = await Annotation.fetch(otherId);
          other.imageGroup = annot.imageGroup;
          await updateTermProperties(other);
          await updateTrackProperties(other);
          await updateAnnotationLinkProperties(other);

          editedAnnots = [other];
        } else {
          editedAnnots = await listAnnotationsInGroup(annot.project, annot.group);
        }
        editedAnnots.forEach(a => {
          this.$eventBus.$emit('editAnnotation', a);
          if (this.copiedAnnot && a.id === this.copiedAnnot.id) {
            let copiedAnnot = this.copiedAnnot.clone();
            copiedAnnot.annotationLink = a.annotationLink;
            copiedAnnot.group = a.group;
            this.copiedAnnot = copiedAnnot;
          }
        });
      }

      this.$eventBus.$emit('deleteAnnotation', annot);
    },

    selectAnnotation({ annot, options }) {
      let index = (options.trySameView) ? this.index : null;
      this.$eventBus.$emit('selectAnnotation', { index, annot, center: true });

      if (this.image.id !== annot.image) {
        this.$store.commit(this.imageModule + 'clearSimilarAnnotations');
      }
    },

    togglePanel(panel) {
      // this.$store.commit(this.imageModule + 'togglePanel', panel);
    },
    centerView({ annot, sameView = false }) {
      if (sameView) {
        this.$emit('centerView', annot);
      } else {
        this.$eventBus.$emit('selectAnnotation', { index: null, annot, center: true });
      }
    }
  },
  beforeDestroy() {
    // this.$store.commit(this.imageModule + 'setShowSimilarAnnotations', false);
  },
};
</script>

<style scoped lang="scss">
@import '../../assets/styles/dark-variables';

.annotations-container {
  position: absolute;
  top: 1.8rem;
  right: 0.1rem;
  width: 20rem;
  height: auto;
  max-height: calc(100vh - 15rem); // 设置最大高度为视窗高度减去顶部偏移
  overflow: visible; // 改为visible，防止内容被裁剪
  overflow-y: visible; // 同样设置为visible

  background-color: $dark-bg-primary;
  color: $dark-text-primary;
  opacity: 0.95;
  border-radius: 1%;
  box-sizing: border-box; // 添加box-sizing以确保padding和border包含在元素的总宽高内
  z-index: 10; // 确保组件在其他元素之上
}

/* Deep-scoped selectors for child components can be added here if needed */
</style>
