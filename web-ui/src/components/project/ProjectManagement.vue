<template>
  <div class="project-management-container">
    <div class="panel-heading">
      <div class="panel-heading-content">
        <strong class="panel-heading-title">Folder View</strong>
        <div class="panel-heading-subtitle">Manage your projects and organize content efficiently</div>
      </div>
    </div>
    <div class="columns is-gapless is-fullheight project-content-area">
      <div class="column is-one-quarter file-tree-column">
        <div class="file-tree-header">
          <h2 class="title is-5">Project Tree</h2>
        </div>
        <div class="file-tree-content">
          <ProjectTree 
            ref="projectTree" 
            @select-item="handleItemSelected" 
            @add-subfolder="openAddImageGroupModal" 
            @rename-item="openRenameModal" 
          />
        </div>
      </div>
      <div class="column content-display-column">
        <ProjectContentDisplay 
          :selected-item="selectedItem" 
          :selected-item-type="selectedItemType" 
          :selected-project="selectedProject" 
          @add-subfolder="openAddImageGroupModal" 
          @add-image="openAddImageModal" 
          @share="openShareModal" 
          @rename="openRenameModal" 
          :revision="revision" 
        />
      </div>
    </div>
    <AddImageGroupModal :active.sync="isAddImageGroupModalActive" @create="createImageGroup" />
    <AddImageModal :active.sync="isAddImageModalActive" :project="selectedProject" :image-group="imageGroupForNewImage" :context="addImageContext" @addImage="handleImageAdded" />
    <ShareProjectModal :active.sync="isShareModalActive" :project="selectedProject" />
    <RenameModal :active.sync="isRenameModalActive" :item-name="itemToRename ? itemToRename.name : ''" @rename="handleRename" />
  </div>
</template>

<script>
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
  data() {
    return {
      selectedItem: null,
      selectedItemType: null,
      selectedProject: null,
      isAddImageGroupModalActive: false,
      isAddImageModalActive: false,
      isShareModalActive: false,
      isRenameModalActive: false,
      projectForNewImageGroup: null,
      imageGroupForNewImage: null,
      itemToRename: null,
      itemToRenameType: null,
      addImageContext: 'project',
      revision: 0,
      all: true
    };
  },
  methods: {
    handleItemSelected(payload) {
      this.selectedItem = payload.item;
      this.selectedItemType = payload.type;
      if (payload.type === 'project') {
        this.selectedProject = payload.item;
      }
      else if (payload.type === 'imageGroup') {
        this.selectedProject = this.findProjectForImageGroup(payload.item);
      }
      console.log('Selected Item:', this.selectedItemType, this.selectedItem, 'in project', this.selectedProject);
    },
    findProjectForImageGroup(imageGroup) {
      const projectId = this.$refs.projectTree.imageGroupProjectMap[imageGroup.id];
      return this.$refs.projectTree.projects.find(p => p.id === projectId);
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
        this.$refs.projectTree.addImageGroup(this.projectForNewImageGroup, newImageGroup);
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
      this.revision++;
    },
    openShareModal() {
      this.closeAllModals();
      this.isShareModalActive = true;
    },
    openRenameModal(payload) {
      this.closeAllModals();
      if(payload) {
        this.itemToRename = payload.item;
        this.itemToRenameType = payload.type;
      } else {
        this.itemToRename = this.selectedItem;
        this.itemToRenameType = this.selectedItemType;
      }
      this.isRenameModalActive = true;
    },
    async handleRename(newName) {
      try {
        this.itemToRename.name = newName;
        if (this.itemToRenameType === 'project') {
          await new Project(this.itemToRename).update();
        }
        else if (this.itemToRenameType === 'imageGroup') {
          await new ImageGroup(this.itemToRename).update();
        }
        this.$refs.projectTree.fetchProjects(); // Refresh the tree
      } catch (error) {
        console.error('Error renaming item:', error);
      } finally {
        this.isRenameModalActive = false;
      }
    }
  }
};
</script>

<style scoped lang="scss">
@import '@/assets/styles/dark-variables.scss';

.project-management-container {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  background-color: $dark-bg-primary;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  margin: 0 1rem;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: linear-gradient(135deg, $dark-bg-secondary 0%, $dark-bg-tertiary 100%);
  border-bottom: 1px solid $dark-border-color;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

  .panel-heading-content {
    display: flex;
    flex-direction: column;
    
    .panel-heading-title {
      font-size: 1.5em;
      color: $dark-text-primary;
      font-weight: 700;
      margin-bottom: 0.25rem;
    }
    
    .panel-heading-subtitle {
      font-size: 0.9em;
      color: $dark-text-secondary;
      opacity: 0.8;
    }
  }

  .panel-heading-actions {
    display: flex;
    gap: 0.75rem;
    
    .button {
      border-radius: 6px;
      transition: all 0.2s ease;
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
      }
      
      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        transform: none;
      }
    }
  }
}

.project-content-area {
  flex-grow: 1;
  margin: 0;
  height: 100%;
  
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

      .tree-filter {
        .button {
          border-radius: 4px;
          padding: 0.25rem 0.75rem;
          font-size: 0.85em;
          
          &.is-primary {
            background-color: $primary;
            border-color: $primary;
            color: $dark-bg-primary;
          }
        }
      }
    }

    .file-tree-content {
      flex-grow: 1;
      overflow-y: auto;
      padding: 0 1.5rem 1.5rem;
    }
  }

  .content-display-column {
    background-color: $dark-bg-primary;
    overflow-y: auto;
    padding: 0;
  }
}

// Scrollbar styling
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: $dark-scrollbar-track;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: $dark-scrollbar-thumb;
  border-radius: 4px;
  &:hover {
    background: $dark-scrollbar-thumb-hover;
  }
}
</style>