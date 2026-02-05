<template>
  <div class="project-content-display">
    <div v-if="!selectedItem" class="has-text-centered">
      <p class="title is-5">Select a project or image group from the tree to view its content.</p>
    </div>
    <div v-else>
      <h3 class="title is-5">{{ selectedItem.name }} ({{ selectedItemType === 'project' ? 'Folder' : 'Sub-folder' }})</h3>

      <div class="field is-grouped is-grouped-right">
        <p class="control" v-if="selectedItemType === 'project'">
          <button class="button" @click="$emit('add-subfolder', selectedItem)">
            <span class="icon is-small"><i class="fas fa-folder-plus"></i></span>
            <span>Create Sub-folder</span>
          </button>
        </p>
        <p class="control">
          <button class="button is-info" @click="$emit('add-image')">
            <span class="icon is-small"><i class="fas fa-plus"></i></span>
            <span>Add Image</span>
          </button>
        </p>
        <p class="control" v-if="selectedItemType === 'project' && !$keycloak.hasTemporaryToken">
          <button class="button is-primary" @click="runAIOnProject(selectedItem)">
            <span class="icon is-small"><i class="fas fa-robot"></i></span>
            <span>Run AI</span>
          </button>
        </p>
        <p class="control">
          <button class="button is-link" @click="$emit('share')">
            <span class="icon is-small"><i class="fas fa-share-alt"></i></span>
            <span>Share</span>
          </button>
        </p>
      </div>

      <div v-if="loading" class="has-text-centered">
        <b-loading :is-full-page="false" :active="loading" />
      </div>

      <div v-else class="columns is-multiline">
        <div class="column is-one-fifth" v-for="group in imageGroups" :key="`group-${group.id}`">
          <div class="card full-height-card">
            <div class="card-image">
              <figure class="image">
                <i class="fas fa-folder"></i> <!-- Folder icon for image groups -->
              </figure>
            </div>
            <div class="card-content">
              <div class="media">
                <div class="media-content">
                  <p class="title is-6">{{ group.name }}</p>
                  <p class="subtitle is-7">Image Group</p>
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

    <!-- Single AI Runner Selection Modal -->
    <SelectAIRunnerModal 
      :active.sync="singleAIRunnerSelectionModal" 
      :ai-runners="aiRunners"
      @confirm="handleAIRunnerSelected"
    />
  </div>
</template>

<script>
import { ImageInstanceCollection, ImageGroupCollection, AIRunner, AIAlgorithmJob } from '@/api';
import ImageCard from '../image/ImageCard.vue';
import SelectAIRunnerModal from './SelectAIRunnerModal.vue';

export default {
  name: 'ProjectContentDisplay',
  components: {
    ImageCard,
    SelectAIRunnerModal
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
      imageGroups: [],
      aiRunners: [],
      singleAIRunnerSelectionModal: false,
      projectToRunAI: null
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
  async created() {
    // Load AI runners when component is created
    try {
      this.aiRunners = await AIRunner.fetchAll();
    } catch (error) {
      console.error('Error fetching AI runners:', error);
      this.aiRunners = [];
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
            filterKey: 'imagegroup',
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
    },

    runAIOnProject(project) {
      // 单个项目运行AI功能
      if (this.aiRunners.length === 0) {
        this.$buefy.toast.open({
          message: this.$t('no-ai-runners-available'),
          type: 'is-danger'
        });
        return;
      }

      this.projectToRunAI = project;
      this.singleAIRunnerSelectionModal = true;
    },

    handleAIRunnerSelected(selectedRunner) {
      this.$buefy.dialog.confirm({
        title: `Confirm whether to run the ${selectedRunner.name} algorithm`,
        message: 'This run will be in the background, so don\'t need to wait for.',
        type: 'is-primary',
        confirmText: this.$t('button-confirm'),
        cancelText: this.$t('button-cancel'),
        onConfirm: async () => {
          try {
            // 为单个项目运行AI算法
            const requestData = {
              airunnerId: selectedRunner.id,
              projectId: this.projectToRunAI.id
            };

            // 调用API运行AI算法
            await AIAlgorithmJob.runAlgorithm(requestData);

            this.$buefy.toast.open({
              message: this.$t('single-ai-processing-started'),
              type: 'is-success'
            });
          } catch (error) {
            console.error('Error running AI algorithm:', error);
            this.$buefy.toast.open({
              message: this.$t('error-running-ai-algorithm'),
              type: 'is-danger'
            });
          }
        }
      });
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

  &.full-height-card {
    height: 100%;
  }

  .card-image {
    background-color: $dark-bg-secondary;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    display: flex;
    justify-content: center;
    align-items: center;

    .fa-folder {
      font-size: 5rem;
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