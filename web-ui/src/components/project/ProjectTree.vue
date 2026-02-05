<template>
  <aside class="menu">
    <div class="menu-heading">
      <p class="menu-label">
        Projects
      </p>
      <div class="actions-bar">
        <div class="buttons has-addons">
          <button class="button is-small" :class="{ 'is-primary': all }" @click="all = true; revision++">
            All
          </button>
          <button class="button is-small" :class="{ 'is-primary': !all }" @click="all = false; revision++">
            My
          </button>
        </div>
      </div>
    </div>
    <ul class="menu-list">
      <li v-for="project in projects" :key="project.id">
        <a @click="toggleProject(project)" @contextmenu.prevent="showContextMenu($event, 'project', project)"
          :class="{'is-active': selectedProject && selectedProject.id === project.id}">
          <span class="icon is-small">
            <i class="fas fa-folder"></i>
          </span>
          <span class="icon is-small">
            <i :class="project.isExpanded ? 'fas fa-angle-down' : 'fas fa-angle-right'"></i>
          </span>
          {{ project.name }}
        </a>
        <ul v-if="project.isExpanded">
          <li v-for="imageGroup in project.imageGroups" :key="imageGroup.id">
            <a @click="selectImageGroup(imageGroup)" @contextmenu.prevent="showContextMenu($event, 'imageGroup', imageGroup)"
              :class="{'is-active': selectedImageGroup && selectedImageGroup.id === imageGroup.id}">
              <span class="icon is-small">
                <i class="fas fa-folder"></i>
              </span>
              {{ imageGroup.name }}
            </a>
          </li>
        </ul>
      </li>
    </ul>
    <ContextMenu ref="contextMenu" :items="contextMenuItems" @item-click="handleMenuItemClick" v-click-outside="closeContextMenu" />
  </aside>
</template>

<script>
import { ProjectCollection, ImageGroupCollection, ImageGroup } from '@/api';
import ContextMenu from './ContextMenu.vue';

export default {
  name: 'ProjectTree',
  components: {
    ContextMenu
  },
  data() {
    return {
      projects: [],
      selectedProject: null,
      selectedImageGroup: null,
      contextMenuItems: [],
      contextMenuItem: null,
      contextMenuType: null,
      all: true,
      revision: 0,
      imageGroupProjectMap: {}
    };
  },
  watch: {
    revision() {
      this.fetchProjects();
    }
  },
  methods: {
    async fetchProjects() {
      try {
        const projectCollection = new ProjectCollection({ all: this.all });
        const fetchedProjects = await projectCollection.fetchAll();
        this.projects = fetchedProjects.array.map(p => ({ ...p, imageGroups: [], isExpanded: false }));
        
        let imageGroupProjectMap = {};
        for (const project of this.projects) {
          const imageGroupCollection = new ImageGroupCollection({
            filterKey: 'project',
            filterValue: project.id
          });
          const fetchedImageGroups = await imageGroupCollection.fetchAll();
          project.imageGroups = fetchedImageGroups.array;
          project.imageGroups.forEach(ig => {
            imageGroupProjectMap[ig.id] = project.id;
          });
        }
        this.imageGroupProjectMap = imageGroupProjectMap;
      } catch (error) {
        console.error('Error fetching projects or image groups:', error);
      }
    },
    toggleProject(project) {
      project.isExpanded = !project.isExpanded;
      this.selectProject(project);
    },
    selectProject(project) {
      this.selectedProject = project;
      this.selectedImageGroup = null;
      this.$emit('select-item', { type: 'project', item: project });
    },
    selectImageGroup(imageGroup) {
      this.selectedImageGroup = imageGroup;
      this.$emit('select-item', { type: 'imageGroup', item: imageGroup });
    },
    showContextMenu(event, type, item) {
      this.contextMenuItem = item;
      this.contextMenuType = type;
      if (type === 'project') {
        this.contextMenuItems = [
          {
            label: 'Add Sub-folder',
            action: 'add-subfolder',
            icon: 'fas fa-folder-plus'
          },
          {
            label: 'Rename',
            action: 'rename',
            icon: 'fas fa-edit'
          }
        ];
      } else if (type === 'imageGroup') {
        this.contextMenuItems = [
          {
            label: 'Rename',
            action: 'rename',
            icon: 'fas fa-edit'
          },
          {
            label: 'Delete',
            action: 'delete',
            icon: 'fas fa-trash'
          }
        ];
      }
      this.$refs.contextMenu.open(event);
    },
    closeContextMenu() {
      if (this.$refs.contextMenu) {
        this.$refs.contextMenu.close();
      }
    },
    handleMenuItemClick(item) {
      this.closeContextMenu();
      if (item.action === 'add-subfolder') {
        this.$emit('add-subfolder', this.contextMenuItem);
      }
      else if (item.action === 'rename') {
        this.$emit('rename-item', { type: this.contextMenuType, item: this.contextMenuItem });
      }
      else if (item.action === 'delete') {
        this.deleteItem(this.contextMenuItem);
      }
    },
    addImageGroup(project, imageGroup) {
      const proj = this.projects.find(p => p.id === project.id);
      if (proj) {
        proj.imageGroups.push(imageGroup);
      }
    },
    deleteItem(item) {
      this.$buefy.dialog.confirm({
        title: `Delete ${this.contextMenuType}`,
        message: `Are you sure you want to delete <strong>${item.name}</strong>? This action cannot be undone.`,
        type: 'is-danger',
        confirmText: 'Delete',
        onConfirm: async () => {
          try {
            if (this.contextMenuType === 'imageGroup') {
              await new ImageGroup({ id: item.id }).delete();
              this.fetchProjects(); // Refresh tree
            }
          } catch (error) {
            console.error(`Error deleting ${this.contextMenuType}:`, error);
          }
        }
      });
    }
  },
  created() {
    this.fetchProjects();
  }
};
</script>

<style scoped lang="scss">
@import '@/assets/styles/dark-variables.scss';

.menu-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.menu-label {
  color: $dark-text-secondary;
  font-size: 0.9em;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.menu-list a {
  color: $dark-text-primary;
  border-radius: 4px;
  transition: all 0.2s ease-in-out;
  display: flex;
  align-items: center;

  &:hover {
    background-color: $dark-bg-hover;
  }

  &.is-active {
    background-color: $dark-bg-active;
    color: $dark-text-primary;
  }

  .icon {
    margin-right: 5px;
  }
}

.menu-list ul {
  margin-left: 1em;
  border-left: 1px solid $dark-border-color;
}
</style>
