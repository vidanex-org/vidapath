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
  <div class="image-selector-container">
    <div class="image-selector-wrapper" :class="{ collapsed: collapsed }">
      <div>
        <div class="card" v-for="image in images" :key="image.id" :class="{active: alreadyAdded(image)}">
          <a
            class="card-image"
            @click="addImage(image)"
            :style="'background-image: url(' + appendShortTermToken(imageThumbUrl(image), shortTermToken) + ')'"
          ></a>
          <div class="card-content" @click="addImage(image)">
           <image-name :image="image" />
          </div>
        </div>
        <!-- <button class="button" v-if="nbImagesDisplayed < nbFilteredImages" @click="more()">
          {{$t('button-more')}}
        </button> -->
        <!-- <div class="space">&nbsp;</div> -->
      </div>
    </div>
    <div class="image-selector-opener" @click="collapsed = !collapsed" :title="collapsed ? $t('expand') : $t('collapse')">
      <i class="fas" :class="collapsed ? 'fa-angle-right' : 'fa-angle-left'"></i>
    </div>
  </div>
</template>

<script>
import {get} from '@/utils/store-helpers';
import {IMAGE_FORMAT} from '@/utils/image-utils';

import ImageName from '@/components/image/ImageName';
import {ImageInstanceCollection} from '@/api';
import _ from 'lodash';
import {appendShortTermToken} from '@/utils/token-utils.js';

export default {
  name: 'image-selector',
  components: {
    ImageName
  },
  data() {
    return {
      images: [],
      nbImagesDisplayed: 20,
      nbFilteredImages: 0,
      loading: true,
      error: false
    };
  },
  computed: {
    project: get('currentProject/project'),
    shortTermToken: get('currentUser/shortTermToken'),
    viewerModule() {
      return this.$store.getters['currentProject/currentViewerModule'];
    },
    // imageSelectorEnabled has been replaced by collapsed state in a-layout-sider
    // The store state is now synchronized with the collapsed property
    collapsed: {
      get() {
        // Initialize from store if available, otherwise use default value
        const viewer = this.$store.getters['currentProject/currentViewer'];
        if (viewer && viewer.imageSelector !== undefined) {
          return !viewer.imageSelector;
        }
        return true; // default to collapsed
      },
      set(value) {
        // Update store when collapsed state changes
        this.$store.commit(this.viewerModule + 'setImageSelector', !value);
      }
    },
    viewerImagesIds() {
      return Object.values(this.$store.getters['currentProject/currentViewer'].images).map(image => image?.imageInstance?.id);
    }
  },
  watch: {
    nbImagesDisplayed() {
      this.fetchImages();
    }
  },
  methods: {
    appendShortTermToken,
    async addImage(image) {
      try {
        // 检查图像是否已经添加到查看器中
        let existingImageIndex = this.viewerImagesIds.indexOf(image.id);
        if (existingImageIndex !== -1) {
          // 如果图像已经存在，切换到该图像
          let imageIndexes = Object.keys(this.$store.getters['currentProject/currentViewer'].images);
          let imageIndex = imageIndexes.find(index => 
            this.$store.getters['currentProject/currentViewer'].images[index].imageInstance.id === image.id
          );
          this.$store.commit(this.viewerModule + 'setActiveImage', imageIndex);
        } else {
          // 如果图像不存在，替换当前活动图像
          await image.fetch(); // refetch image to ensure we have latest version
          let slice = await image.fetchReferenceSlice();
          let activeImageIndex = this.$store.getters['currentProject/currentViewer'].activeImage;
          await this.$store.dispatch(`${this.viewerModule}images/${activeImageIndex}/setImageInstance`, {image, slices: [slice]});
        }
      } catch (error) {
        console.log(error);
        // this.$notify({type: 'error', text: this.$t('notif-error-add-viewer-image')});
      }
    },
    async fetchImages(loading = true) {
      if (loading) {
        this.loading = true;
      }

      try {
        let collection = new ImageInstanceCollection({
          filterKey: 'project',
          filterValue: this.project.id,
          max: this.nbImagesDisplayed,
          sort: 'id',
          order: 'asc',
        });

        let data = (await collection.fetchPage(0));
        this.images = data.array;
        this.nbFilteredImages = data.totalNbItems;
      } catch (error) {
        console.log(error);
        this.error = true;
      }
      if (loading) {
        this.loading = false;
      }
    },

    more() {
      this.nbImagesDisplayed += 20;
    },

    toggle() {
      this.collapsed = !this.collapsed;
    },

    shortkeyHandler(key) {
      if (key === 'toggle-add-image') {
        this.toggle();
      }
    },

    alreadyAdded(image) {
      return this.viewerImagesIds.includes(image.id);
    },
    imageThumbUrl(image) {
      return image.thumbURL(256, IMAGE_FORMAT);
    }
  },
  async created() {
    this.loading = true;
    await this.fetchImages(false);
    this.loading = false;
  },
  mounted() {
    this.$eventBus.$on('shortkeyEvent', this.shortkeyHandler);
  },
  beforeDestroy() {
    this.$eventBus.$off('shortkeyEvent', this.shortkeyHandler);
  }
};
</script>

<style scoped lang="scss">
@import '../../assets/styles/dark-variables';

/* 定义滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: $dark-wapper-bg !important;
}

::-webkit-scrollbar-thumb {
  background: $dark-scrollbar-thumb !important;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: $dark-scrollbar-thumb-hover !important;
}

.image-selector-container {
  display: flex;
  height: 100%;
}

.image-selector-wrapper {
  background-color: $dark-wapper-bg;
  box-shadow: 0 2px 3px rgba(10, 10, 10, 0.1), 0 0 0 1px rgba(10, 10, 10, 0.1);
  display: flex;
  flex-direction: column;
  width: 14em;
  height: 100%;
  z-index: 150;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: 1px solid $dark-border-color;
  transition: width 0.3s ease, min-width 0.3s ease, padding 0.3s ease;
}

.image-selector-wrapper.collapsed {
  width: 0;
  min-width: 0;
  border-right: none;
  overflow: hidden;
}

.image-selector-opener {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.2rem;
  background-color: $dark-bg-secondary;
  border-right: 1px solid $dark-border-color;
  cursor: pointer;
  color: $dark-text-secondary;
  z-index: 151;
}

.image-selector-opener:hover {
  background-color: $dark-bg-tertiary;
  color: $dark-text-primary;
}

.card {
  margin: 0.25em;
}

.card-image {
  display: inline-block;
  width: 100%;
  height: 9.5em;
  background-position: center center;
  background-size: cover;
  background-repeat: no-repeat;
  background-color: transparent;
  border-radius: 8px;
}

.card-content {
  padding: 0.5em;
  font-size: 0.9rem;
  overflow: hidden;
  text-align: center;
}
</style>
