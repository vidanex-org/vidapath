<template>
  <div class="project-management-container">
    <div class="columns is-gapless project-content-area">
      <div class="column is-one-quarter file-tree-column">
        <div class="file-tree-header">
          <h2 class="title is-5">Folder Tree</h2>
        </div>
        <div class="file-tree-content">
          <ProjectTree 
            ref="projectTree" 
            :selected-item="selectedItem"
            :selected-item-type="selectedItemType"
            @select-item="handleItemSelected" 
            @add-subfolder="openAddImageGroupModal" 
            @rename-item="openRenameModal" 
            @delete-item="handleDeleteItem"
            @refresh-projects="fetchProjects"
          />
        </div>
      </div>
      <div class="column content-display-column">
        <ProjectContentDisplay 
          :selected-item="selectedItem" 
          :selected-item-type="selectedItemType" 
          :selected-project="selectedProject"
          :content-loading="contentLoading"
          :content-images="contentImages"
          :content-image-groups="contentImageGroups"
          @select-item="handleItemSelected"
          @add-subfolder="openAddImageGroupModal" 
          @add-image="openAddImageModal" 
          @share="openShareModal" 
          @rename="openRenameModal"
          @delete-image="handleDeleteImage"
          @refresh-projects="fetchContent"
        />
      </div>
    </div>
    <AddImageGroupModal :active.sync="isAddImageGroupModalActive" @create="createImageGroup" />
    <AddImageModal 
      :active.sync="isAddImageModalActive" 
      :project="selectedProject" 
      :image-group="imageGroupForNewImage" 
      :context="addImageContext" 
      @addImage="handleImageAdded" 
    />
    <ShareProjectModal :active.sync="isShareModalActive" :project="selectedProject" />
    <RenameModal :active.sync="isRenameModalActive" :item-name="itemToRename ? itemToRename.name : ''" @rename="handleRename" />
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex';
import { ImageGroup, Project } from '@/api';
import ProjectTree from './ProjectTree.vue';
import ProjectContentDisplay from './ProjectContentDisplay.vue';
import AddImageGroupModal from './AddImageGroupModal.vue';
import AddImageModal from '../image/AddImageModal.vue';
import ShareProjectModal from './ShareProjectModal.vue';
import RenameModal from './RenameModal.vue';

export default {
  name: 'ProjectManagement',
  components: {
    ProjectTree,
    ProjectContentDisplay,
    AddImageGroupModal,
    AddImageModal,
    ShareProjectModal,
    RenameModal
  },
  computed: {
    ...mapState('project-tree', [
      'selectedItem', 
      'selectedItemType', 
      'selectedProject', 
    ]),
    ...mapGetters('project-tree', [
      'contentLoading',
      'contentImages',
      'contentImageGroups',
      'findProjectForImageGroup'
    ])
  },
  methods: {
    ...mapActions('project-tree', [
      'fetchProjects', 
      'fetchContent'
    ]),
    
    handleItemSelected(payload) {
      this.$store.commit('project-tree/SET_SELECTED_ITEM', payload);
      if (payload.type === 'project') {
        this.$store.commit('project-tree/SET_SELECTED_PROJECT', payload.item);
      }
      else if (payload.type === 'imageGroup') {
        // Ensure we get the actual project object, not a promise
        const project = this.findProjectForImageGroup(payload.item);
        if (project) {
          this.$store.commit('project-tree/SET_SELECTED_PROJECT', project);
        }
      }
      console.log('Selected Item:', payload.type, payload.item, 'in project', this.selectedProject);
      // Fetch content when selection changes
      this.fetchContent();
    },
    
    async handleDeleteItem(payload) {
      if (payload.type === 'imageGroup') {
        this.$buefy.dialog.confirm({
          title: `Delete ${payload.type}`,
          message: `Are you sure you want to delete <b>${payload.item.name}</b>? This action cannot be undone.`,
          type: 'is-danger',
          confirmText: 'Delete',
          onConfirm: async () => {
            try {
              await new ImageGroup({ id: payload.item.id }).delete();
              this.fetchProjects();
            } catch (error) {
              console.error(`Error deleting ${payload.type}:`, error);
            }
          }
        });
      }
    },
    
    async handleDeleteImage(imageId) {
      this.$buefy.dialog.confirm({
        title: 'Delete Image',
        message: 'Are you sure you want to delete this image? This action cannot be undone.',
        type: 'is-danger',
        confirmText: 'Delete',
        onConfirm: async () => {
          try {
            // Find the image in current content and remove it
            const imageIndex = this.contentImages.findIndex(img => img.id === imageId);
            if (imageIndex !== -1) {
              // In a real implementation, you would call the API to delete the image
              // For now, we'll just remove it from the local state
              // await new ImageInstance({ id: imageId }).delete();
              this.$store.commit('project-tree/SET_CONTENT_DATA', {
                images: this.contentImages.filter(img => img.id !== imageId),
                imageGroups: this.contentImageGroups
              });
            }
          } catch (error) {
            console.error('Error deleting image:', error);
          }
        }
      });
    },
    
    closeAllModals() {
      this.isAddImageGroupModalActive = false;
      this.isAddImageModalActive = false;
      this.isShareModalActive = false;
      this.isRenameModalActive = false;
    },
    
    openAddImageGroupModal(project) {
      this.closeAllModals();
      this.projectForNewImageGroup = project || this.selectedProject;
      this.isAddImageGroupModalActive = true;
    },
    
    async createImageGroup(name) {
      try {
        const newImageGroup = new ImageGroup({
          name: name,
          project: this.projectForNewImageGroup.id
        });
        await newImageGroup.save();
        this.$store.commit('project-tree/ADD_IMAGE_GROUP_TO_PROJECT', { 
          project: this.projectForNewImageGroup, 
          imageGroup: newImageGroup 
        });
        this.fetchProjects();
      } catch (error) {
        console.error('Error creating image group:', error);
      } finally {
        this.isAddImageGroupModalActive = false;
      }
    },
    
    openAddImageModal() {
      this.closeAllModals();
      if(this.selectedItemType === 'imageGroup') {
        this.addImageContext = 'imageGroup';
        this.imageGroupForNewImage = this.selectedItem;
      } else {
        this.addImageContext = 'project';
        this.imageGroupForNewImage = null;
      }
      this.isAddImageModalActive = true;
    },
    
    handleImageAdded() {
      this.fetchContent();
    },
    
    openShareModal() {
      this.closeAllModals();
      this.isShareModalActive = true;
    },
    
    openRenameModal(payload) {
      this.closeAllModals();
      if(payload) {
        // Create a copy of the item to avoid modifying store state directly
        this.itemToRename = {...payload.item};
        this.itemToRenameType = payload.type;
      } else {
        // Create a copy of the selected item to avoid modifying store state directly
        this.itemToRename = {...this.selectedItem};
        this.itemToRenameType = this.selectedItemType;
      }
      this.isRenameModalActive = true;
    },
    
    async handleRename(newName) {
      try {
        // Update the copied item's name
        this.itemToRename.name = newName;
        if (this.itemToRenameType === 'project') {
          await new Project(this.itemToRename).update();
        }
        else if (this.itemToRenameType === 'imageGroup') {
          await new ImageGroup(this.itemToRename).update();
        }
        this.fetchProjects();
      } catch (error) {
        console.error('Error renaming item:', error);
      } finally {
        this.isRenameModalActive = false;
      }
    }
  },
  
  data() {
    return {
      isAddImageGroupModalActive: false,
      isAddImageModalActive: false,
      isShareModalActive: false,
      isRenameModalActive: false,
      projectForNewImageGroup: null,
      imageGroupForNewImage: null,
      itemToRename: null,
      itemToRenameType: null,
      addImageContext: 'project'
    };
  },
  
  created() {
    this.fetchProjects();
  },
  
  watch: {
    selectedItem: {
      immediate: true,
      handler() {
        this.fetchContent();
      }
    },
  }
};
</script>

<style scoped lang="scss">
@import '@/assets/styles/dark-variables.scss';

.project-management-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: $dark-bg-primary;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  margin: 0 1rem;
}



.project-content-area {
  flex-grow: 1;
  margin: 0;
  
  .file-tree-column {
    background-color: $dark-bg-secondary;
    padding: 0;
    border-right: 1px solid $dark-border-color;
    display: flex;
    flex-direction: column;
    min-width: 280px;
    max-width: 320px;

    .file-tree-header {
      padding: 1.5rem 1.5rem 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid $dark-border-color;

      .title {
        color: $dark-text-primary;
        margin: 0;
        font-weight: 600;
      }
    }

    .file-tree-content {
      flex-grow: 1;
      padding: 0 1.5rem 1.5rem;

      &::-webkit-scrollbar {
        width: 6px;
      }

      &::-webkit-scrollbar-track {
        background: transparent;
      }

      &::-webkit-scrollbar-thumb {
        background: $dark-scrollbar-thumb;
        border-radius: 3px;
        &:hover {
          background: $dark-scrollbar-thumb-hover;
        }
      }
    }
  }

  .content-display-column {
    background-color: $dark-bg-primary;
    padding: 1.5rem;
    flex-grow: 1;
  }
}

@media (max-width: 768px) {
  .file-tree-column {
    max-width: 100%;
    border-right: none;
    border-bottom: 1px solid $dark-border-color;
  }
}
</style>