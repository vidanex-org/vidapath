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
<cytomine-modal :active="active" :title="$t('add-images')" @close="$emit('update:active', false)">
  <b-loading :is-full-page="false" :active="loading" class="small" />
  <template v-if="!loading">
    <template>
      <b-input class="search-images" v-model="searchString" :placeholder="$t('search-placeholder')"
      type="search" icon="search" />

      <cytomine-table
        :collection="imageCollection"
        :currentPage.sync="currentPage"
        :perPage.sync="perPage"
        :sort.sync="sortField"
        :order.sync="sortOrder"
        :detailed="false"
      >
        <template #default="{row: image}">
          <b-table-column :label="$t('overview')">
            <image-thumbnail :image="image" :size="128" :key="`${image.id}-thumb-128`" :extra-parameters="{Authorization: 'Bearer ' + shortTermToken }"/>
          </b-table-column>

          <b-table-column :field="context === 'project' ? 'originalFilename' : 'instanceFilename'" :label="$t('name')" sortable>
            {{ context === 'project' ? image.originalFilename : image.instanceFilename }}
          </b-table-column>

          <b-table-column field="created" :label="$t('created-on')" sortable>
            {{ Number(image.created) | moment('ll LT') }}
          </b-table-column>

          <b-table-column label=" " centered>
            <button v-if="wasAdded(image)" class="button is-small is-link" disabled>
              {{$t('button-added')}}
            </button>
            <button v-else-if="isInGroupOrProject(image)" class="button is-small is-link" disabled>
              {{ context === 'project' ? $t('already-in-project') : $t('already-in-group') }}
            </button>
            <button v-else class="button is-small is-link" @click="addImage(image)">
              {{$t('button-add')}}
            </button>
          </b-table-column>
        </template>

        <template #empty>
          <div class="content has-text-grey has-text-centered">
            <p>{{$t('no-image')}}</p>
          </div>
        </template>
      </cytomine-table>
    </template>
  </template>
</cytomine-modal>
</template>

<script>
import {get} from '@/utils/store-helpers';
import {AbstractImageCollection, ImageInstanceCollection, ImageInstance, ImageGroupImageInstance} from '@/api';
import CytomineModal from '@/components/utils/CytomineModal';
import CytomineTable from '@/components/utils/CytomineTable';
import ImageThumbnail from '@/components/image/ImageThumbnail';

export default {
  name: 'add-image-modal',
  props: {
    active: Boolean,
    project: Object,
    imageGroup: {
      type: Object,
      default: null
    },
    context: {
      type: String,
      default: 'project'
    }
  },
  components: {
    ImageThumbnail,
    CytomineTable,
    CytomineModal
  },
  data() {
    return {
      loading: true,
      perPage: 10,
      searchString: '',
      idsAddedImages: [],
      imageIdsInGroup: [],
      currentPage: 1,
      sortField: 'created',
      sortOrder: 'desc',
    };
  },
  computed: {
    shortTermToken: get('currentUser/shortTermToken'),
    imageCollection() {
      let collection;
      if (this.context === 'project') {
        // 添加空值保护
        if (!this.project) {
          return new AbstractImageCollection();
        }
        collection = new AbstractImageCollection({project: this.project.id});
        if (this.searchString) {
          collection['originalFilename'] = {ilike: encodeURIComponent(this.searchString)};
        }
      } else { // imageGroup context
        // 添加空值保护
        if (!this.project) {
          return new ImageInstanceCollection();
        }
        collection = new ImageInstanceCollection({
          filterKey: 'project',
          filterValue: this.project.id,
        });
        if (this.searchString) {
          collection['instanceFilename'] = {ilike: encodeURIComponent(this.searchString)};
        }
      }
      return collection;
    },
  },
  watch: {
    async active(val) {
      if (val) {
        this.idsAddedImages = [];
        if (this.context === 'imageGroup') {
          await this.fetchImageIdsInGroup();
        }
      }
    }
  },
  methods: {
    async fetchImageIdsInGroup() {
      if (!this.imageGroup) {
        this.imageIdsInGroup = [];
        return;
      }
      try {
        const images = await new ImageInstanceCollection({
          filterKey: 'imagegroup',
          filterValue: this.imageGroup.id
        }).fetchAll();
        this.imageIdsInGroup = images.array.map(image => image.id);
      } catch (error) {
        console.error('Error fetching images in group:', error);
        this.imageIdsInGroup = [];
      }
    },
    async addImage(image) {
      if (this.context === 'project') {
        let propsTranslation = {imageName: image.originalFilename, projectName: this.project.name};
        try {
          let newImage = await new ImageInstance({baseImage: image.id, project: this.project.id}).save();
          this.idsAddedImages.push(image.id);
          this.$emit('addImage', newImage);
          this.$notify({
            type: 'success',
            text: this.$t('notif-success-add-image', propsTranslation)
          });
          let updatedProject = this.project.clone();
          updatedProject.numberOfImages++;
          this.$store.dispatch('currentProject/updateProject', updatedProject);
        } catch (error) {
          console.log(error);
          this.$notify({
            type: 'error',
            text: this.$t('notif-error-add-image', propsTranslation)
          });
        }
      }
      else { // imageGroup context
        try {
          await new ImageGroupImageInstance({group: this.imageGroup.id, image: image.id}).save();
          this.idsAddedImages.push(image.id);
          this.$emit('addImage', image);
          this.$notify({
            type: 'success',
            text: this.$t('notif-success-add-image-to-group', {imageName: image.instanceFilename, groupName: this.imageGroup.name})
          });
        } catch (error) {
          console.log(error);
          this.$notify({
            type: 'error',
            text: this.$t('notif-error-add-image-to-group', {imageName: image.instanceFilename, groupName: this.imageGroup.name})
          });
        }
      }
    },
    isInGroupOrProject(image) {
      if (this.context === 'project') {
        return image.inProject;
      } else {
        return this.imageIdsInGroup.includes(image.id);
      }
    },
    wasAdded(image) {
      return this.idsAddedImages.includes(image.id);
    }
  },
  async created() {
    if(this.active) {
      if (this.context === 'imageGroup') {
        await this.fetchImageIdsInGroup();
      }
    }
    this.loading = false;
  }
};
</script>

<style scoped lang="scss">
@import "../../assets/styles/dark-variables.scss";

>>> .animation-content {
  max-width: 60% !important;
  width: 60%;
}

>>> .modal-card {
  width: 100%;
  height: 80vh;
  background-color: $dark-bg-primary;
}

>>> .modal-card-title {
  color: $dark-text-primary;
  background-color: $dark-bg-secondary;
  border-color: $dark-border-color;
}

>>> .modal-card-body {
  background-color: $dark-bg-primary;
  color: $dark-text-primary;
}

>>> .modal-card-foot {
  background-color: $dark-bg-secondary;
  border-color: $dark-border-color;
}

>>> .image-thumbnail {
  max-height: 4rem;
  max-width: 10rem;
}

/* 暗黑模式下的表格样式 */
>>> .table {
  background-color: $dark-bg-primary;
  color: $dark-text-primary;
}

>>> .table tr {
  background-color: $dark-bg-primary;
  color: $dark-text-primary;
}

>>> .table tr:hover {
  background-color: $dark-bg-hover;
}

>>> .table th {
  background-color: $dark-bg-secondary;
  color: $dark-text-primary;
  border-color: $dark-border-color;
}

>>> .table td {
  color: $dark-text-primary;
  border-color: $dark-border-color;
}

/* 暗黑模式下的输入框 */
>>> .input {
  background-color: $dark-input-bg;
  color: $dark-text-primary;
  border-color: $dark-input-border;
}

>>> .input::placeholder {
  color: $dark-text-disabled;
}

>>> .input:focus {
  border-color: $dark-input-focus-border;
  box-shadow: 0 0 0 0.2rem $dark-input-focus-shadow;
}

/* 暗黑模式下的按钮 */
>>> .button {
  background-color: $dark-button-bg;
  color: $dark-text-primary;
  border-color: $dark-button-border;
}

>>> .button:hover {
  background-color: $dark-button-hover-bg;
  border-color: $dark-button-hover-border;
}

>>> .button.is-link {
  background-color: $dark-button-bg;
  color: $dark-text-primary;
  border-color: $dark-button-border;
}

>>> .button.is-link:hover {
  background-color: $dark-button-hover-bg;
  border-color: $dark-button-hover-border;
}

>>> .button.is-small {
  background-color: $dark-button-bg;
  color: $dark-text-primary;
  border-color: $dark-button-border;
}

>>> .button.is-small:hover {
  background-color: $dark-button-hover-bg;
  border-color: $dark-button-hover-border;
}

/* 暗黑模式下的分页控件 */
>>> .pagination {
  background-color: $dark-bg-secondary;
  color: $dark-text-primary;
}

>>> .pagination .button {
  background-color: $dark-button-bg;
  color: $dark-text-primary;
  border-color: $dark-button-border;
}

>>> .pagination .button:hover {
  background-color: $dark-button-hover-bg;
  border-color: $dark-button-hover-border;
}

>>> .pagination .button[disabled] {
  background-color: $dark-bg-tertiary;
  color: $dark-text-disabled;
  border-color: $dark-border-color;
}

/* 暗黑模式下的加载动画 */
>>> .loading {
  background-color: rgba(30, 30, 30, 0.7);
  color: $dark-text-primary;
}

</style>