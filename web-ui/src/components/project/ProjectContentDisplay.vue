<template>
  <div class="project-content-display">
    <div v-if="!selectedItem" class="empty-selection-state">
      <div class="empty-icon">
        <i class="fas fa-folder-tree"></i>
      </div>
      <p class="subtitle is-6 empty-subtitle">Choose an item from the folder tree to view and manage its content.</p>
    </div>
    <div v-else class="content-wrapper">
      <div class="content-header">
        <div class="content-title-section">
          <h3 class="title is-5 content-title">
            <span class="folder-icon"><i class="fas fa-folder"></i></span>
            {{ selectedItem.name }}
            <span class="content-type-badge" :class="`is-${selectedItemType === 'project' ? 'warning' : 'info'}`">
              {{ selectedItemType === 'project' ? 'Folder' : 'Sub-folder' }}
            </span>
          </h3>
        </div>

        <div class="content-actions">
          <div class="field is-grouped">
            <p class="control" v-if="selectedItemType === 'project'">
              <button 
                class="button is-outlined is-warning" 
                @click="$emit('add-subfolder', selectedItem)"
                title="Create a new sub-folder"
              >
                <span class="icon is-small"><i class="fas fa-folder-plus"></i></span>
                <span>Sub-folder</span>
              </button>
            </p>
            <p class="control">
              <button 
                class="button is-outlined is-info" 
                @click="$emit('add-image')"
                title="Add new images to this folder"
              >
                <span class="icon is-small"><i class="fas fa-plus"></i></span>
                <span>Add Image</span>
              </button>
            </p>
            <p class="control" v-if="selectedItemType === 'project' && !$keycloak.hasTemporaryToken">
              <button 
                class="button is-outlined is-primary" 
                @click="runAIOnProject(selectedItem)"
                title="Run AI analysis on all images in this project"
              >
                <span class="icon is-small"><i class="fas fa-robot"></i></span>
                <span>Run AI</span>
              </button>
            </p>
            <p class="control">
              <button 
                class="button is-outlined is-link" 
                @click="$emit('share')"
                title="Share this folder with others"
              >
                <span class="icon is-small"><i class="fas fa-share-alt"></i></span>
                <span>Share</span>
              </button>
            </p>
            <p class="control">
              <button
                class="button is-outlined"
                @click="$emit('rename')"
                title="Rename this folder"
              >
                <span class="icon is-small"><i class="fas fa-edit"></i></span>
                <span>Rename</span>
              </button>
            </p>
            <p class="control">
              <button
                class="button is-outlined is-success"
                @click="showDetailsModal = true"
                title="View folder details"
              >
                <span class="icon is-small"><i class="fas fa-info-circle"></i></span>
                <span>Details</span>
              </button>
            </p>
          </div>
        </div>
      </div>

      <div v-if="loading" class="loading-container">
        <b-loading :is-full-page="false" :active="loading" />
      </div>

      <div v-else class="content-grid">
        <div 
          v-if="imageGroups.length > 0" 
          class="section-header"
        >
          <h4 class="subtitle is-6">Folders ({{ imageGroups.length }})</h4>
        </div>
        
        <div class="columns is-multiline image-groups-grid">
          <div 
            class="column is-one-quarter" 
            v-for="group in imageGroups" 
            :key="`group-${group.id}`"
          >
            <div 
              class="card folder-card"
              @click="selectImageGroup(group)"
            >
              <div class="card-image">
                <figure class="image">
                  <i class="fas fa-folder folder-icon-large"></i>
                </figure>
              </div>
              <div class="card-content">
                <div class="media">
                  <div class="media-content">
                    <p class="title is-6 folder-name">{{ group.name }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div 
          v-if="images.length > 0" 
          class="section-header"
        >
          <h4 class="subtitle is-6">Images ({{ images.length }})</h4>
        </div>
        
        <div class="columns is-multiline images-grid">
                    <ImageCard
                      v-for="(image, index) in images"
                      :key="`image-${image.id}`"
                      :image="image"
                      :project="selectedProject"
                      :context="selectedItemType"
                      @delete="handleImageDelete(index)"
                    />        </div>

        <div 
          v-if="!loading && images.length === 0 && imageGroups.length === 0" 
          class="empty-content-state"
        >
          <div class="empty-icon">
            <i class="fas fa-inbox"></i>
          </div>
          <p class="empty-text">This folder is empty</p>
          <p class="empty-hint">Add images or create sub-folders to get started</p>
        </div>
      </div>
    </div>

    <!-- Folder Details Modal -->
    <div v-if="showDetailsModal" class="modal is-active folder-details-modal">
      <div class="modal-background" @click="showDetailsModal = false"></div>
      <div class="modal-card" style="max-width: 800px; width: 90%;">
        <header class="modal-card-head">
          <p class="modal-card-title">
            <span class="icon is-small">
              <i class="fas fa-folder"></i>
            </span>
            {{ selectedItemType === 'project' ? 'Folder' : 'Sub-folder' }} Details
          </p>
          <button class="delete" aria-label="close" @click="showDetailsModal = false"></button>
        </header>
        <section class="modal-card-body">
          <b-loading :is-full-page="false" :active="detailsLoading" />
          <div v-if="!detailsLoading">
            <table class="table is-fullwidth properties-table">
              <tbody>
                <tr>
                  <td class="prop-label">Name</td>
                  <td class="prop-content">{{ selectedItem.name }}</td>
                </tr>
                <tr v-if="selectedItemType === 'project'">
                  <td class="prop-label">Total Images</td>
                  <td class="prop-content">{{ selectedItem.numberOfImages || images.length }}</td>
                </tr>
                <tr v-if="selectedItemType === 'imageGroup'">
                  <td class="prop-label">Images in this folder</td>
                  <td class="prop-content">{{ images.length }}</td>
                </tr>
                <tr v-if="selectedItemType === 'project'">
                  <td class="prop-label">Sub-folders</td>
                  <td class="prop-content">{{ imageGroups.length }}</td>
                </tr>
                <tr v-if="selectedItemType === 'project'">
                  <td class="prop-label">User Annotations</td>
                  <td class="prop-content">{{ selectedItem.numberOfAnnotations || 0 }}</td>
                </tr>
                <tr>
                  <td class="prop-label">Description</td>
                  <td class="prop-content">
                    <cytomine-description :object="modelInstance" :canEdit="canEdit" />
                  </td>
                </tr>
                <tr v-if="selectedItemType === 'project'">
                  <td class="prop-label">Tags</td>
                  <td class="prop-content">
                    <cytomine-tags :object="modelInstance" :canEdit="canEdit" />
                  </td>
                </tr>
                <tr v-if="selectedItemType === 'project'">
                  <td class="prop-label">Attached Files</td>
                  <td class="prop-content">
                    <attached-files :object="modelInstance" :canEdit="canEdit" />
                  </td>
                </tr>
                <tr>
                  <td class="prop-label">Created On</td>
                  <td class="prop-content">
                    {{ Number(selectedItem.created) | moment('ll') }}
                  </td>
                </tr>
                <tr v-if="selectedItemType === 'project' && representatives.length > 0">
                  <td class="prop-label">Assigned Users ({{ representatives.length }})</td>
                  <td class="prop-content">
                    <list-usernames :users="representatives" :onlines="onlines" />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
        <footer class="modal-card-foot" style="justify-content: flex-end;">
          <button class="button" @click="showDetailsModal = false">Close</button>
        </footer>
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
import { ImageInstanceCollection, ImageGroupCollection, ImageGroup, Project, AIRunner, AIAlgorithmJob } from '@/api';
import { get } from '@/utils/store-helpers';
import ImageCard from '../image/ImageCard.vue';
import SelectAIRunnerModal from './SelectAIRunnerModal.vue';
import CytomineDescription from '@/components/description/CytomineDescription';
import CytomineTags from '@/components/tag/CytomineTags';
import AttachedFiles from '@/components/attached-file/AttachedFiles';
import ListUsernames from '@/components/user/ListUsernames';

export default {
  name: 'ProjectContentDisplay',
  components: {
    ImageCard,
    SelectAIRunnerModal,
    CytomineDescription,
    CytomineTags,
    AttachedFiles,
    ListUsernames
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
      projectToRunAI: null,
      showDetailsModal: false,
      detailsLoading: false,
      representatives: [],
      onlines: []
    };
  },
  computed: {
    currentUser: get('currentUser/user'),
    canEdit() {
      return !this.$keycloak.hasTemporaryToken && this.selectedItem;
    },
    // Wrap selectedItem into proper API model instance
    modelInstance() {
      if (!this.selectedItem) {
        return null;
      }
      if (this.selectedItemType === 'project') {
        return new Project(this.selectedItem);
      } else if (this.selectedItemType === 'imageGroup') {
        return new ImageGroup(this.selectedItem);
      }
      return null;
    }
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
    },
    showDetailsModal(newVal) {
      if (newVal && this.selectedItem && this.selectedItemType === 'project') {
        this.fetchProjectDetails();
      }
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
    },

    async fetchProjectDetails() {
      if (this.selectedItemType !== 'project') {
        return;
      }

      this.detailsLoading = true;
      try {
        // Fetch representatives
        this.representatives = (await this.selectedItem.fetchRepresentatives()).array;
        // Fetch online users
        this.onlines = await this.selectedItem.fetchConnectedUsers();
      } catch (error) {
        console.error('Error fetching project details:', error);
      } finally {
        this.detailsLoading = false;
      }
    },

    selectImageGroup(group) {
      this.$emit('select-item', { type: 'imageGroup', item: group });
    },

    handleImageDelete(index) {
      this.images.splice(index, 1);
    }
  }
};
</script>

<style scoped lang="scss">
@import '@/assets/styles/dark-variables.scss';

.project-content-display {
  
  .empty-selection-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: $dark-text-disabled;
    
    .empty-icon {
      font-size: 4rem;
      margin-bottom: 1.5rem;
      opacity: 0.4;
    }
    
    .empty-title {
      color: $dark-text-secondary;
      margin-bottom: 0.5rem;
    }
    
    .empty-subtitle {
      color: $dark-text-disabled;
      opacity: 0.8;
    }
  }
  
  .content-wrapper {
    
    .content-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 1.5rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid $dark-border-color;
      
      .content-title-section {
        .content-title {
          color: $dark-text-primary;
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin: 0;
          
          .folder-icon {
            color: $warning;
            font-size: 1.2em;
          }
          
          .content-type-badge {
            font-size: 0.75em;
            padding: 0.25em 0.5em;
            border-radius: 4px;
            font-weight: 600;
            
            &.is-warning {
              background-color: rgba($warning, 0.2);
              color: $warning;
            }
            
            &.is-info {
              background-color: rgba($info, 0.2);
              color: $info;
            }
          }
        }
      }
      
      .content-actions {
        .button {
          border-radius: 6px;
          padding: 0.5em 0.75em;
          font-size: 0.85em;
          transition: all 0.2s ease;
          
          &:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          }
          
          .icon {
            margin-right: 0.375em;
          }
        }
      }
    }
    
    .loading-container {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 200px;
    }
    
    .content-grid {
      .section-header {
        margin: 1.5rem 0 1rem;
        
        .subtitle {
          color: $dark-text-secondary;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          opacity: 0.8;
        }
      }
      
      .image-groups-grid,
      .images-grid {
        margin-left: -0.75rem;
        margin-right: -0.75rem;
      }
      
      .folder-card {
        background-color: $dark-bg-panel;
        border-radius: 8px;
        transition: all 0.2s ease;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
        
        &:hover {
          transform: translateY(-4px);
          box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
          border-color: $primary;
          
          .folder-icon-large {
            color: $primary;
          }
        }
        
        .card-image {
          background-color: $dark-bg-secondary;
          border-top-left-radius: 8px;
          border-top-right-radius: 8px;
          display: flex;
          justify-content: center;
          align-items: center;
          padding: 1.5rem;
          flex-shrink: 0;
          
          .folder-icon-large {
            font-size: 3rem;
            color: $warning;
          }
        }
        
        .card-content {
          .folder-name {
            color: $dark-text-primary;
            font-weight: 600;
            font-size: 0.95em;
            text-align: center;
          }
        }
      }
      
      .empty-content-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3rem 1rem;
        text-align: center;
        color: $dark-text-disabled;
        
        .empty-icon {
          font-size: 3rem;
          margin-bottom: 1rem;
          opacity: 0.4;
        }
        
        .empty-text {
          font-size: 1.2rem;
          font-weight: 500;
          margin-bottom: 0.5rem;
          color: $dark-text-secondary;
        }
        
        .empty-hint {
          opacity: 0.7;
        }
      }
    }
  }
}

.properties-table {
  background-color: transparent;

  td {
    border: 1px solid $dark-border-color;
    vertical-align: top;

    &.prop-label {
      background-color: $dark-bg-secondary;
      color: $dark-text-secondary;
      font-weight: 600;
      width: 30%;
      padding: 0.75rem 1rem;
    }

    &.prop-content {
      background-color: $dark-bg-primary;
      color: $dark-text-primary;
      padding: 0.75rem 1rem;
    }
  }
}

// Folder Details Modal styling
.folder-details-modal {
  z-index: 40; // Standard modal z-index

  .modal-card {
    border-radius: 8px;
    overflow: hidden;
  }

  .modal-card-head {
    background-color: $dark-bg-secondary;
    border-bottom: 1px solid $dark-border-color;

    .modal-card-title {
      color: $dark-text-primary;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
  }

  .modal-card-body {
    background-color: $dark-bg-primary;
    max-height: 70vh;
    overflow-y: auto;
  }

  .modal-card-foot {
    background-color: $dark-bg-secondary;
    border-top: 1px solid $dark-border-color;
  }
}

@media (max-width: 768px) {
  .content-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .content-actions {
    margin-top: 1rem;
    width: 100%;

    .field.is-grouped {
      flex-wrap: wrap;
      justify-content: flex-start;
    }
  }

  .folder-details-modal .modal-card {
    max-width: 95% !important;
  }
}
</style>