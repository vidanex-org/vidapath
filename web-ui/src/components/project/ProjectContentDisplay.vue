<template>
  <div class="project-content-display">
    <div v-if="!selectedItem" class="has-text-centered">
      <p class="title is-5">Select a project or image group from the tree to view its content.</p>
    </div>
    <div v-else>
      <h3 class="title is-5">{{ selectedItem.name }} ({{ selectedItemType === 'project' ? 'Project' : 'Image Group' }})</h3>

      <div class="field is-grouped is-grouped-right">
        <p class="control">
          <button class="button is-info" @click="$emit('add-image')">
            <span class="icon is-small"><i class="fas fa-plus"></i></span>
            <span>Add Image</span>
          </button>
        </p>
        <p class="control">
          <button class="button is-warning" @click="$emit('rename')">
            <span class="icon is-small"><i class="fas fa-edit"></i></span>
            <span>Rename</span>
          </button>
        </p>
        <p class="control">
          <button class="button is-primary" @click="$emit('share')">
            <span class="icon is-small"><i class="fas fa-share-alt"></i></span>
            <span>Share</span>
          </button>
        </p>
        <p class="control" v-if="selectedItemType === 'project'">
          <button class="button is-success" @click="$emit('add-subfolder', selectedItem)">
            <span class="icon is-small"><i class="fas fa-folder-plus"></i></span>
            <span>Create Folder (Image Group)</span>
          </button>
        </p>
      </div>

      <div v-if="loading" class="has-text-centered">
        <b-loading :is-full-page="false" :active="loading" />
      </div>

      <div v-else class="columns is-multiline">
        <div class="column is-one-quarter" v-for="group in imageGroups" :key="`group-${group.id}`">
          <div class="card">
            <div class="card-image">
              <figure class="image is-4by3">
                <i class="fas fa-folder fa-5x"></i> <!-- Folder icon for image groups -->
              </figure>
            </div>
            <div class="card-content">
              <div class="media">
                <div class="media-content">
                  <p class="title is-5">{{ group.name }}</p>
                  <p class="subtitle is-6">Image Group</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <ImageCard v-for="image in images" :key="`image-${image.id}`" :image="image" :project="selectedProject" />
      </div>

      <div v-if="!loading && images.length === 0 && imageGroups.length === 0" class="has-text-centered">
        <p>No content to display.</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ImageInstanceCollection, ImageGroupCollection } from '@/api';
import ImageCard from '../image/ImageCard.vue';

export default {
  name: 'ProjectContentDisplay',
  components: {
    ImageCard
  },
  props: {
    selectedItem: {
      type: Object,
      default: null
    },
    selectedItemType: {
      type: String,
      default: null
    },
    selectedProject: {
      type: Object,
      default: null
    },
    revision: {
      type: Number,
      default: 0
    }
  },
  data() {
    return {
      loading: false,
      images: [],
      imageGroups: []
    };
  },
  watch: {
    selectedItem: {
      immediate: true,
      handler() {
        this.fetchContent();
      }
    },
    revision() {
      this.fetchContent();
    }
  },
  methods: {
    async fetchContent() {
      this.loading = true;
      this.images = [];
      this.imageGroups = [];

      if (!this.selectedItem) {
        this.loading = false;
        return;
      }

      try {
        if (this.selectedItemType === 'project') {
          // Fetch image groups for the project
          const imageGroupCollection = new ImageGroupCollection({
            filterKey: 'project',
            filterValue: this.selectedItem.id
          });
          const fetchedImageGroups = await imageGroupCollection.fetchAll();
          this.imageGroups = fetchedImageGroups.array;

          // Fetch images for the project (not belonging to any image group directly)
          const imageInstanceCollection = new ImageInstanceCollection({
            filterKey: 'project',
            filterValue: this.selectedItem.id
          });
          const fetchedImages = await imageInstanceCollection.fetchAll();
          this.images = fetchedImages.array.filter(image => !image.imageGroup);
        } else if (this.selectedItemType === 'imageGroup') {
          // Fetch images for the image group
          const imageInstanceCollection = new ImageInstanceCollection({
            filterKey: 'imageGroup',
            filterValue: this.selectedItem.id
          });
          const fetchedImages = await imageInstanceCollection.fetchAll();
          this.images = fetchedImages.array;
        }
      } catch (error) {
        console.error('Error fetching content:', error);
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped lang="scss">
@import '@/assets/styles/dark-variables.scss';

.project-content-display {
  padding: 1rem;

  .title {
    color: $dark-text-primary;
  }
}

.card {
  background-color: $dark-bg-panel;
  color: $dark-text-primary;
  border-radius: 8px;
  box-shadow: 0 2px 3px rgba(10, 10, 10, 0.1), 0 0 0 1px rgba(10, 10, 10, 0.1);

  .card-image {
    background-color: $dark-bg-secondary;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;

    .fa-folder {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100%;
      color: $warning;
    }
  }

  .card-content {
    .title, .subtitle {
      color: $dark-text-primary;
    }
  }
}
</style>
