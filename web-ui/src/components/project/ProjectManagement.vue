<template>
  <div class="project-management-container">
    <div class="columns is-gapless">
      <div class="column is-one-quarter file-tree-column">
        <h2 class="title is-4">Project Tree</h2>
        <ProjectTree ref="projectTree" @select-item="handleItemSelected" @add-subfolder="openAddImageGroupModal" @rename-item="openRenameModal" />
      </div>
      <div class="column content-display-column">
        <ProjectContentDisplay :selected-item="selectedItem" :selected-item-type="selectedItemType" :selected-project="selectedProject" @add-subfolder="openAddImageGroupModal" @add-image="openAddImageModal" @share="openShareModal" @rename="openRenameModal" :revision="revision" />
      </div>
    </div>
    <AddImageGroupModal :active.sync="isAddImageGroupModalActive" @create="createImageGroup" />
    <AddImageModal :active.sync="isAddImageModalActive" :project="selectedProject" @addImage="handleImageAdded" />
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
      itemToRename: null,
      itemToRenameType: null,
      revision: 0
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
      for (const project of this.$refs.projectTree.projects) {
        if (project.imageGroups.some(ig => ig.id === imageGroup.id)) {
          return project;
        }
      }
      return null;
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
  height: calc(100vh - 100px); /* Adjust based on your header and switcher height */
  display: flex;
  flex-direction: column;
}

.columns {
  flex-grow: 1;
  margin-left: 0;
  margin-right: 0;
}

.file-tree-column {
  background-color: $dark-bg-secondary;
  padding: 1rem;
  border-right: 1px solid $dark-border-color;
  overflow-y: auto;

  .title {
    color: $dark-text-primary;
  }
}

.content-display-column {
  background-color: $dark-bg-primary;
  overflow-y: auto;
}
</style>
