<template>
  <aside class="project-tree-menu">
    <div class="tree-header">
      <div class="tree-filter">
        <div class="field has-addons">
          <p class="control">
            <button 
              class="button is-small" 
              :class="{ 'is-primary': all }" 
              @click="all = true; revision++"
            >
              All
            </button>
          </p>
          <p class="control">
            <button 
              class="button is-small" 
              :class="{ 'is-primary': !all }" 
              @click="all = false; revision++"
            >
              My
            </button>
          </p>
        </div>
      </div>
    </div>
    <ul class="menu-list">
      <li v-for="project in projects" :key="project.id" class="project-item">
        <a 
          @click="toggleProject(project)" 
          @contextmenu.prevent="showContextMenu($event, 'project', project)"
          :class="{'is-active': !isImageGroupSelected && selectedProject && selectedProject.id === project.id}"
          class="project-link"
        >
          <span class="icon is-small expand-icon">
            <i :class="project.isExpanded ? 'fas fa-angle-down' : 'fas fa-angle-right'"></i>
          </span>
          <span class="icon is-small folder-icon">
            <i class="fas fa-folder"></i>
          </span>
          <span class="project-name">{{ project.name }}</span>
        </a>
        <ul v-if="project.isExpanded" class="image-group-list">
          <li v-for="imageGroup in project.imageGroups" :key="imageGroup.id" class="image-group-item">
            <a 
              @click="selectImageGroup(imageGroup)" 
              @contextmenu.prevent="showContextMenu($event, 'imageGroup', imageGroup)"
              :class="{'is-active': selectedImageGroup && selectedImageGroup.id === imageGroup.id}"
              class="image-group-link"
            >
              <span class="icon is-small folder-icon">
                <i class="fas fa-folder"></i>
              </span>
              <span class="image-group-name">{{ imageGroup.name }}</span>
            </a>
          </li>
        </ul>
      </li>
    </ul>
    <div v-if="projects.length === 0" class="empty-state">
      <div class="empty-icon">
        <i class="fas fa-folder-open"></i>
      </div>
      <p class="empty-text">No projects found</p>
    </div>
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
      imageGroupProjectMap: {},
      isImageGroupSelected: false
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
        
        // 自动选择第一个项目（如果存在且当前没有选中的项目）
        if (this.projects.length > 0 && !this.selectedProject && !this.selectedImageGroup) {
          this.selectProject(this.projects[0]);
        }
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
      this.isImageGroupSelected = false;
    },
    selectImageGroup(imageGroup) {
      this.selectedImageGroup = imageGroup;
      this.$emit('select-item', { type: 'imageGroup', item: imageGroup });
      this.isImageGroupSelected = true;
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
        message: `Are you sure you want to delete <b>${item.name}</b>? This action cannot be undone.`,
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

.project-tree-menu {
  height: 100%;
  
  .tree-header {
    padding: 0 0 1rem 0;
    border-bottom: 1px solid $dark-border-color;
    margin-bottom: 1rem;
    
    .tree-filter {
      display: flex;
      justify-content: flex-end;
      
      .button {
        border-radius: 4px;
        padding: 0.25rem 0.75rem;
        font-size: 0.85em;
        margin-left: 0.25rem;
        
        &.is-primary {
          background-color: $primary;
          border-color: $primary;
          color: $dark-bg-primary;
        }
      }
    }
  }
  
  .menu-list {
    margin: 0;
    padding: 0;
    
    .project-item {
      margin-bottom: 0.5rem;
      
      .project-link {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        transition: all 0.2s ease;
        color: $dark-text-primary;
        text-decoration: none;
        font-weight: 500;
        position: relative;
        
        &:hover {
          background-color: $dark-bg-hover;
          transform: translateX(4px);
        }
        
        &.is-active {
          background-color: rgba($primary, 0.2);
          border-left: 3px solid $primary;
          color: $primary;
          
          .folder-icon i {
            color: $primary;
          }
        }
        
        .expand-icon {
          margin-right: 8px;
          opacity: 0.7;
          transition: transform 0.2s ease;
        }
        
        .folder-icon {
          margin-right: 10px;
          color: $warning;
        }
        
        .project-name {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      }
      
      .image-group-list {
        margin: 0.5rem 0 0 1.5rem;
        padding: 0;
        list-style: none;
        
        .image-group-item {
          margin-bottom: 0.25rem;
          
          .image-group-link {
            display: flex;
            align-items: center;
            padding: 0.5rem 0.75rem;
            border-radius: 4px;
            transition: all 0.2s ease;
            color: $dark-text-secondary;
            text-decoration: none;
            font-size: 0.95em;
            
            &:hover {
              background-color: $dark-bg-hover;
              color: $dark-text-primary;
            }
            
            &.is-active {
              background-color: rgba($info, 0.2);
              color: $info;
              
              .folder-icon i {
                color: $info;
              }
            }
            
            .folder-icon {
              margin-right: 8px;
              color: $warning;
            }
            
            .image-group-name {
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
            }
          }
        }
      }
    }
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem 1rem;
    color: $dark-text-disabled;
    
    .empty-icon {
      font-size: 2.5rem;
      margin-bottom: 1rem;
      opacity: 0.6;
    }
    
    .empty-text {
      font-size: 0.9rem;
      opacity: 0.8;
    }
  }
}

// Scrollbar styling
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: $dark-scrollbar-thumb;
  border-radius: 3px;
  &:hover {
    background: $dark-scrollbar-thumb-hover;
  }
}
</style>