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
  <div class="annotations-list-panel-container">
    <div class="box">
      <h2> Annotations list </h2>
      <div class="filters">
        <div class="columns">
          <div class="column filter">
            <div class="filter-label">
              {{$t('terms')}}
            </div>
            <div class="filter-body">
              <ontology-tree-multiselect
                :ontologys="ontologies"
                :additionalNodes="additionalTermNodes"
                v-model="selectedTermsIds"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="annotations-list" @scroll="scrollHandler" ref="listAnnots">
      <list-annotations-by v-for="prop in limitedCategoryOptions" :key="`${selectedCategorization.categorization}${prop.id}`"
        :categorization="selectedCategorization.categorization"
        :size="selectedSize.size"
        :color="selectedColor.hexaCode"
        :nbPerPage="nbPerPage"
        :bundling="regroup.bundling"

        :allTerms="terms"

        :prop="prop"
        :multiple-terms="(isByTerm && prop.id === multipleTermsOption.id)"
        :no-term="(isByTerm && prop.id === noTermOption.id) || (!isByTerm && noTerm)"
        :terms-ids="selectedTermsIds"


        :revision="revision"

        v-show="showList(prop)"
        :visible="showList(prop)"
        @updateTermsOrTracks="revision++"
        @select="viewAnnot($event)"
      />
      <button class="button" v-if="!areAllOptionsLoaded" @click="loadCategories()">
        <span class="icon">
          <i class="fas fa-sync"></i>
        </span>
        <span>{{$t('button-load-more')}}</span>
      </button>
    </div>
  </div>
</template>

<script>
import { get } from '@/utils/store-helpers';
import constants from '@/utils/constants.js';
import OntologyTreeMultiselect from '@/components/ontology/OntologyTreeMultiselect';
import ListAnnotationsBy from '@/components/annotations/ListAnnotationsBy';
import { UserCollection, AnnotationCollection, TrackCollection, TagCollection } from '@/api';
import { defaultColors } from '@/utils/style-utils.js';
import _ from 'lodash';

const categoryBatch = constants.CATEGORY_ITEMS_PER_BATCH;

export default {
  name: 'annotations-list-panel',
  props: {
    index: String
  },
  components: {
    OntologyTreeMultiselect,
    ListAnnotationsBy
  },
  data() {
    return {
      revision: 0,

      projectUsers: [],
      tracks: [],

      selectedSize: {label: this.$t('small'), size: 85},
      selectedCategorization: {label: this.$t('per-term'), categorization: 'TERM'},
      nbPerPage: 10,
      selectedColor: {label: this.$t('default-color'), hexaCode: '#0000ff'},
      selectedAnnotationType: null,
      selectedMembers: [],
      selectedReviewers: [],
      selectedImages: [],
      selectedImageGroups: [],
      selectedTags: [],
      selectedTracksIds: [],
      selectedTermsIds: [],
      regroup: {label: this.$t('no'), bundling: 'NO'},

      noTermOption: {id: 0, name: this.$t('no-term')},
      multipleTermsOption: {id: -1, name: this.$t('multiple-terms')},
      nLoadedOptionsPerCategory: {
        'TERM': constants.ANNOTATIONS_MAX_ITEMS_PER_CATEGORY,
        'IMAGE': constants.ANNOTATIONS_MAX_ITEMS_PER_CATEGORY,
        'USER': constants.ANNOTATIONS_MAX_ITEMS_PER_CATEGORY,
        'TRACK': constants.ANNOTATIONS_MAX_ITEMS_PER_CATEGORY,
        'UNCATEGORIZED': constants.ANNOTATIONS_MAX_ITEMS_PER_CATEGORY
      },
    };
  },
  computed: {
    currentUser: get('currentUser/user'),
    project: get('currentProject/project'),
    blindMode() {
      return this.project.blindMode;
    },
    canManageProject() {
      return this.$store.getters['currentProject/canManageProject'];
    },

    imageModule() {
      return this.$store.getters['currentProject/imageModule'](this.index);
    },

    imageWrapper() {
      return this.$store.getters['currentProject/currentViewer'].images[this.index];
    },
    // 使用图像的本体而不是项目的本体
    ontologies() {
      return this.imageWrapper.ontologies || [];
    },

    terms() {
      return this.$store.getters[this.imageModule + 'terms'];
    },

    additionalTermNodes() {
      let additionalNodes = [this.noTermOption];
      if (this.terms.length > 1 && this.isByTerm) {
        additionalNodes.push(this.multipleTermsOption);
      }
      return additionalNodes;
    },
    termsOptions() {
      return this.terms.concat(this.additionalTermNodes);
    },

    categoryOptions() {
      return this.termsOptions;
    },
    limitedCategoryOptions() {
      return this.categoryOptions.slice(0, this.nLoadedOptionsPerCategory[this.selectedCategorization.categorization]);
    },
    areAllOptionsLoaded() {
      return this.categoryOptions.length === this.limitedCategoryOptions.length;
    },
    isByTerm() {
      return this.selectedCategorization.categorization === 'TERM';
    },
    noTerm() {
      return this.selectedTermsIds.includes(this.noTermOption.id);
    },

    collection() {
      let collection = new AnnotationCollection({
        project: this.project.id,
        terms: this.selectedTermsIds.length === this.termsOptions.length ? null : this.selectedTermsIds,
        images: this.images,
        users: null,
        reviewed: false,
        reviewUsers: null,
        noTerm: this.noTerm,
        multipleTerms: this.selectedTermsIds.includes(this.multipleTermsOption.id),
        afterThan: null,
        beforeThan: null
      });

      return collection;
    },
    images() {
      // 返回当前图像实例
      return [this.image.id];
    },
    image() {
      return this.$store.getters[this.imageModule + 'imageInstance'];
    },
  },
  methods: {
    scrollHandler: _.debounce(function () {
      let scrollBlock = this.$refs.listAnnots;
      let actualScrollPos = scrollBlock.scrollTop + scrollBlock.clientHeight;

      if (actualScrollPos === scrollBlock.scrollHeight && !this.areAllOptionsLoaded) {
        console.log('Loading new categories from scroll handler.');
        this.loadCategories();
      }
    }, 100),
    loadCategories() {
      const newCount = this.limitedCategoryOptions.length + categoryBatch;
      if (newCount >= this.categoryOptions.length) {
        this.nLoadedOptionsPerCategory[this.selectedCategorization.categorization] = this.categoryOptions.length;
      } else {
        this.nLoadedOptionsPerCategory[this.selectedCategorization.categorization] = newCount;
      }
    },
    viewAnnot(data) {
      this.$router.push(`/project/${this.project.id}/image/${data.annot.image}/annotation/${data.annot.id}`);
    },

    showList(prop) {
      return this.selectedTermsIds.includes(prop.id);
    }
  },
  async created() {
    this.selectedAnnotationType = this.$t('user-annotations');
  
  },
};
</script>

<style scoped lang="scss">
@import '../../../assets/styles/dark-variables';

.annotations-list-panel-container {
  width: 70vw;
  overflow: auto;
}

.annotations-list {
  max-height: 40vh;
  overflow: auto;
  margin-bottom: 1em;
  
  // Custom scrollbar
  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  &::-webkit-scrollbar-track {
    background: $dark-scrollbar-track;
  }

  &::-webkit-scrollbar-thumb {
    background: $dark-scrollbar-thumb;
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: $dark-scrollbar-thumb-hover;
  }
}

.button {
  display: block;
  margin: auto;
}

.box {
  background-color: $dark-bg-primary;
  border: 1px solid $dark-border-color;
  color: $dark-text-primary;
}
</style>