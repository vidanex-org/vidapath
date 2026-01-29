<template>
  <div class="annotations-list-wrapper">
    <div v-if="opened" class="annotations-list-opened">
      <button class="delete" @click="opened = false"></button>

      <div class="annotations-list-sidebar">
        <ontology-tree v-model="selectedTermsIds" :ontologies="ontologies" :multiple-selection="false"
          :hidden-nodes="hiddenTermsIds" :additional-nodes="[noTermOption]" />
      </div>

      <div class="annotations-list-container">
        <list-annotations-by v-if="currentItem" :key="currentItem.id" :categorization="displayType" :size="85"
          color="000000" :nb-per-page="nbPerPage" :prop="currentItem" :all-terms="terms" :all-users="allUsers"
          :all-images="images" :all-tracks="tracks" :multiple-terms="false" :no-term="noTerm" :multiple-track="false"
          :no-track="noTrack" :images-ids="[image.id]" :slices-ids="sliceIds" :users-ids="layersIds"
          :terms-ids="termsOptionsIds" :tracks-ids="tracksIds" :reviewed="false" :visible="opened" :index="index"
          :revision="revision" :show-details="showDetails" @updateTermsOrTracks="$emit('updateTermsOrTracks', $event)"
          @updateProperties="$emit('updateProperties')"
          @centerView="$emit('centerView', { annot: $event, sameView: isSameView($event) })"
          @delete="$emit('delete', $event)" @select="select" />
        <div v-else class="has-text-centered p-4" style="color: #888;">
          <p>No term selected (currentItem is {{ currentItem }})</p>
        </div>
      </div>
    </div>
    <div v-show="!opened" class="opener" @click="opened = true">
      {{ $t("annotations-list") }}
      <i class="fas fa-caret-up"></i>
    </div>
  </div>
</template>

<script>
import { UserCollection } from '@/api';

import { get } from '@/utils/store-helpers';

import ListAnnotationsBy from '@/components/annotations/ListAnnotationsBy';
import OntologyTree from '@/components/ontology/OntologyTree';

export default {
  name: 'annotations-list',
  components: {
    ListAnnotationsBy,
    OntologyTree,
  },
  props: [
    'index',
  ],
  data() {
    return {
      nbPerPage: 20,
      noTermOption: { id: 0, name: this.$t('no-term') },
      users: [],
      revision: 0
    };
  },
  computed: {
    configUI: get('currentProject/configUI'),

    imageModule() {
      return this.$store.getters['currentProject/imageModule'](this.index);
    },
    imageWrapper() {
      return this.$store.getters['currentProject/currentViewer'].images[this.index];
    },
    viewerWrapper() {
      return this.$store.getters['currentProject/currentViewer'];
    },
    image() {
      return this.imageWrapper.imageInstance;
    },
    images() {
      return [this.image];
    },
    isActiveImage() {
      return this.viewerWrapper.activeImage === this.index;
    },
    slices() {
      return this.imageWrapper.activeSlices;
    },
    sliceIds() {
      return this.slices.map(slice => slice.id);
    },

    isDisplayedByTerm() {
      return this.displayType === 'TERM';
    },
    currentItem() {
      return this.termsOptions.find(term => term.id === this.selectedTermId);
    },

    additionalNodes() {
      return [this.noTermOption];
    },
    terms() {
      return this.$store.getters[this.imageModule + 'terms'] || [];
    },
    ontologies() {
      return this.$store.getters[this.imageModule + 'ontologies'];
    },
    hiddenTermsIds() {
      return this.$store.getters[this.imageModule + 'hiddenTermsIds'] || [];
    },
    termsOptions() {
      return [...this.terms, ...this.additionalNodes].filter(term => !this.hiddenTermsIds.includes(term.id));
    },
    termsOptionsIds() {
      return this.termsOptions.map(term => term.id);
    },

    selectedTermId() {
      return (this.selectedTermsIds.length > 0) ? this.selectedTermsIds[0] : null;
    },
    noTerm() {
      return this.isDisplayedByTerm ? this.selectedTermId === this.noTermOption.id : this.termsOptionsIds.includes(this.noTermOption.id);
    },

    tracks() {
      return this.imageWrapper.tracks.tracks;
    },
    tracksIds() {
      let optionsIds = this.tracks.map(track => track.id);
      optionsIds.push(0); // Add 0 for "no track" option
      return optionsIds;
    },
    hasTracks() {
      return this.tracks.length > 0;
    },
    selectedTrackId() {
      return (this.selectedTracksIds.length > 0) ? this.selectedTracksIds[0] : null;
    },
    noTrack() {
      return this.isDisplayedByTerm;
    },

    layers() {
      let layers = this.imageWrapper.layers.selectedLayers || [];
      layers = layers.filter(layer => layer.visible);
      return layers;
    },
    layersIds() {
      return this.layers.map(layer => layer.id);
    },
    allUsers() {
      return this.users.concat(this.userJobs);
    },

    opened: {
      get() {
        console.log('opened', this.imageWrapper);
        return this.imageWrapper.annotationsList.open;
      },
      set(value) {
        this.$store.commit(this.imageModule + 'setShowAnnotationsList', value);
      }
    },

    displayType: {
      get() {
        return this.imageWrapper.annotationsList.displayType;
      },
      set(value) {
        this.$store.commit(this.imageModule + 'setDisplayType', value);
      }
    },

    selectedTermsIds: {
      get() {
        return this.imageWrapper.annotationsList.selectedTermsIds;
      },
      set(value) {
        this.$store.commit(this.imageModule + 'setSelectedTermsIds', value);
      }
    },

    selectedTracksIds: {
      get() {
        return this.imageWrapper.annotationsList.selectedTracksIds;
      },
      set(value) {
        this.$store.commit(this.imageModule + 'setSelectedTracksIds', value);
      }
    },

    showDetails() {
      return this.configUI['project-explore-annotation-main'];
    }
  },
  watch: {
    hasTracks(value) {
      if (!value) {
        this.displayType = 'TERM';
      }
    },
    currentItem: {
      handler(val) {
        console.log('AnnotationsList currentItem changed:', val);
      },
      immediate: true
    }
  },
  methods: {
    async fetchUsers() { // TODO in vuex (project module)
      this.users = (await UserCollection.fetchAll()).array;
    },
    addAnnotationHandler(annotation) {
      if (annotation.image === this.image.id) {
        this.revision++;
      }
    },
    reloadAnnotationsHandler(idImage) {
      if (idImage === null || idImage === this.image.id) {
        this.revision++;
      }
    },
    editAnnotationHandler(updatedAnnot) {
      if (updatedAnnot.image === this.image.id) {
        this.revision++;
      }
    },
    deleteAnnotationHandler(deletedAnnot) {
      if (deletedAnnot.image === this.image.id) {
        this.revision++;
      }
    },
    isSameView(annot) {
      return this.displayType === 'TERM' && this.sliceIds.includes(annot.slice);
    },
    select({ annot, options }) {
      this.$emit('select', { annot, options: { trySameView: options.trySameView || this.isSameView(annot) } });
    },

    shortkeyHandler(key) {
      if (!this.isActiveImage) {
        return;
      }

      if (key === 'toggle-annotations') {
        this.opened = !this.opened;
      }
    }
  },
  async created() {
    if (this.selectedTermsIds.length === 0) {
      this.selectedTermsIds = (this.termsOptionsIds.length > 0) ? [this.termsOptionsIds[0]] : [];
    }
    if (this.selectedTracksIds.length === 0) {
      this.selectedTracksIds = (this.hasTracks) ? [this.tracks[0].id] : [];
    }

    await this.fetchUsers();
  },
  mounted() {
    this.$eventBus.$on('addAnnotation', this.addAnnotationHandler);
    this.$eventBus.$on('reloadAnnotations', this.reloadAnnotationsHandler);
    this.$eventBus.$on('editAnnotation', this.editAnnotationHandler);
    this.$eventBus.$on('deleteAnnotation', this.deleteAnnotationHandler);
    this.$eventBus.$on('shortkeyEvent', this.shortkeyHandler);
  },
  beforeDestroy() {
    // unsubscribe from all events
    this.$eventBus.$off('addAnnotation', this.addAnnotationHandler);
    this.$eventBus.$off('reloadAnnotations', this.reloadAnnotationsHandler);
    this.$eventBus.$off('editAnnotation', this.editAnnotationHandler);
    this.$eventBus.$off('deleteAnnotation', this.deleteAnnotationHandler);
    this.$eventBus.$off('shortkeyEvent', this.shortkeyHandler);
  }
};
</script>

<style scoped lang="scss">
@import '../../assets/styles/dark-variables';

.annotations-list-opened {
  box-shadow: 0 2px 3px rgba(10, 10, 10, 0.5), 0 0 0 1px rgba(10, 10, 10, 0.5);
  background: $dark-bg-secondary;
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  z-index: 40;
  pointer-events: none;
  height: 25vh;
  width: 80%;
  overflow-y: auto;
  pointer-events: auto;
  display: flex;
  color: $dark-text-primary;
  font-size: $details-font-size;
}

.delete {
  position: absolute;
  right: 25px;
  top: 7px;
  z-index: 10;
  color: $dark-text-primary;
}

.annotations-list-container {
  overflow: auto;
  position: relative;
  border-bottom: 1px solid $dark-border-color;
  height: 100%;
  flex-grow: 1;
  background-color: $dark-bg-primary;
  color: $dark-text-primary;
}

.opener {
  background: $dark-bg-secondary;
  width: 150px;
  border-radius: 5px 5px 0px 0px;
  box-shadow: 0 2px 3px rgba(10, 10, 10, 0.5), 0 0 0 1px rgba(10, 10, 10, 0.5);
  margin: auto;
  text-align: center;
  text-transform: uppercase;
  font-size: 10px;
  letter-spacing: 0.3px;
  cursor: pointer;
  pointer-events: auto;
  color: $dark-text-primary;
}

.opener .fas {
  margin-left: 5px;
  font-size: 12px;
  line-height: 10px;
}

.box {
  background: unset;
  border-radius: unset;
  box-shadow: unset;
  padding: 0.75rem;
  height: 100%;
}

h2 {
  color: $dark-text-primary;
  margin-bottom: 0;
}

.annotations-list-sidebar {
  // padding: 10px;
  overflow-y: auto;
  min-width: 15em;
  flex-shrink: 0;
  background-color: $dark-bg-tertiary;
  color: $dark-text-primary;
  font-size: $details-font-size;
}

:deep(ul.pagination-list) {
  justify-content: flex-end;
}

/* 深色模式滚动条样式 */
.annotations-list-opened::-webkit-scrollbar,
.annotations-list-container::-webkit-scrollbar,
.annotations-list-sidebar::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.annotations-list-opened::-webkit-scrollbar-track,
.annotations-list-container::-webkit-scrollbar-track,
.annotations-list-sidebar::-webkit-scrollbar-track {
  background: $dark-scrollbar-track;
}

.annotations-list-opened::-webkit-scrollbar-thumb,
.annotations-list-container::-webkit-scrollbar-thumb,
.annotations-list-sidebar::-webkit-scrollbar-thumb {
  background: $dark-scrollbar-thumb;
  border-radius: 4px;
}

.annotations-list-opened::-webkit-scrollbar-thumb:hover,
.annotations-list-container::-webkit-scrollbar-thumb:hover,
.annotations-list-sidebar::-webkit-scrollbar-thumb:hover {
  background: $dark-scrollbar-thumb-hover;
}

/* 深色模式下的组件样式 */
.annotations-list-opened :deep(.table) {
  background-color: $dark-table-bg;
  color: $dark-text-primary;
}

.annotations-list-opened :deep(.table td),
.annotations-list-opened :deep(.table th) {
  border-color: $dark-table-border;
}

.annotations-list-opened :deep(.table tr:hover) {
  background-color: $dark-table-hover-bg;
}

.annotations-list-opened :deep(.button) {
  background-color: $dark-button-bg;
  color: $dark-text-primary;
  border: 1px solid $dark-button-border;
}

.annotations-list-opened :deep(.button:hover) {
  background-color: $dark-button-hover-bg;
  border-color: $dark-button-hover-border;
}

.annotations-list-opened :deep(.input),
.annotations-list-opened :deep(.textarea),
.annotations-list-opened :deep(.select select) {
  background-color: $dark-input-bg;
  color: $dark-text-primary;
  border-color: $dark-input-border;
}

.annotations-list-opened :deep(.input::placeholder),
.annotations-list-opened :deep(.textarea::placeholder),
.annotations-list-opened :deep(.select select::placeholder) {
  color: $dark-text-disabled;
}

.annotations-list-opened :deep(.input:focus),
.annotations-list-opened :deep(.textarea:focus),
.annotations-list-opened :deep(.select select:focus) {
  border-color: $dark-input-focus-border;
  box-shadow: 0 0 0 0.2rem $dark-input-focus-shadow;
}

.annotations-list-opened :deep(.tag) {
  background-color: $dark-tag-bg;
  color: $dark-text-primary;
  border: 1px solid $dark-tag-border;
}
</style>
