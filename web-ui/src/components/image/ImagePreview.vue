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
  <div class="card" :class="{ 'full-height-card': fullHeightCard }">
    <a class="card-image recent-image" @click="handleNavigation">
      <img :src="imageUrl" class="image-preview-fit">
    </a>
    <div class="card-content">
      <div class="content image-info">
        <div class="image-header">
          <div class="image-name">{{ image.instanceFilename || image.imageName }}</div>
          <button
            class="info-button"
            @click.prevent="$emit('show-details')"
            title="View details"
          >
            <span class="icon is-small">
              <i class="fas fa-info-circle"></i>
            </span>
          </button>
        </div>
        <div class="image-details">
          <div class="info-item" v-if="tissue">
            <span class="info-label">Tissue:</span>
            <span class="info-value">{{ tissue }}</span>
          </div>
          <div class="info-item" v-if="specimen">
            <span class="info-label">Specimen:</span>
            <span class="info-value">{{ specimen }}</span>
          </div>
          <div class="info-item" v-if="stain">
            <span class="info-label">Stain:</span>
            <span class="info-value">{{ stain }}</span>
          </div>
        </div>
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script>
import { changeImageUrlFormat } from '@/utils/image-utils';
import { get } from '@/utils/store-helpers';
import { appendShortTermToken } from '@/utils/token-utils.js';

export default {
  name: 'image-preview',
  props: {
    image: { type: Object },
    project: { type: Object, default: null },
    fullHeightCard: { type: Boolean, default: true },
    showProject: { type: Boolean, default: true },
    blindMode: { type: Boolean, default: false },
  },
  computed: {
    shortTermToken: get('currentUser/shortTermToken'),
    idImage() {
      return this.image.image || this.image.id; // if provided object is image consultation, image.image
    },
    idProject() {
      return (this.project) ? this.project.id : this.image.project;
    },
    isBlindMode() {
      return (this.project) ? this.project.blindMode : this.blindMode;
    },
    rawPreviewUrl() {
      return this.image.thumb || this.image.imageThumb;
    },
    previewUrl() {
      return changeImageUrlFormat(this.rawPreviewUrl);
    },
    imageUrl() {
      return appendShortTermToken(this.previewUrl, this.shortTermToken);
    },
    tissue() {
      // Return fixed value for now, can be made dynamic later
      return '';
    },
    specimen() {
      // Return fixed value for now, can be made dynamic later
      return '';
    },
    stain() {
      // Return fixed value for now, can be made dynamic later
      return '';
    }
  },
  methods: {
    handleNavigation() {
      let groupId = null;
      const projectTreeState = this.$store.state['project-tree'];

      if (projectTreeState.selectedItemType === 'imageGroup') {
        groupId = projectTreeState.selectedItem.id;
      }

      console.log('[DEBUG] ImagePreview Click: Current item type in store:', projectTreeState.selectedItemType);
      console.log('[DEBUG] ImagePreview Click: Dispatching imageGroup ID:', groupId);

      this.$store.dispatch('project-tree/setActiveImageGroupForViewer', groupId);
      this.$router.push(`/project/${this.idProject}/image/${this.idImage}`);
    }
  },
};
</script>

<style scoped lang="scss">
@import "../../assets/styles/dark-variables.scss";

.image-preview-fit {
  object-fit: contain;
  width: 95%;
  height: auto;
  border-bottom: 1px solid $dark-border-color;
  cursor: pointer;
  display: block;
  margin: 0.5rem auto;
}

.card.full-height-card {
  height: 100%;
  background-color: $dark-bg-primary !important;
}

.card-content {
  padding: 0.5rem;
  overflow-wrap: break-word;
}

.card-content a {
  font-weight: 0.8em;
}

.blind-indication {
  font-size: 0.9em;
  text-transform: uppercase;
}

.image-info {
  color: white;
  font-size: 0.9rem;
}

.image-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
  gap: 0.5rem;
}

.image-name {
  font-weight: bold;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.info-button {
  background-color: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  flex-shrink: 0;

  &:hover {
    background-color: $primary;
    border-color: $primary;
    color: white;
  }

  &:active {
    transform: scale(0.95);
  }

  .icon {
    font-size: 0.9rem;
  }
}

.image-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.info-item {
  display: flex;
}

.info-label {
  font-weight: bold;
  margin-right: 5px;
  flex-shrink: 0;
}

.info-value {
  flex-grow: 1;
}
</style>