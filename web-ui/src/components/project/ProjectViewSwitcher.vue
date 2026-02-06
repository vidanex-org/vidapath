<template>
  <div class="project-view-switcher">
    <!-- View content -->
    <div class="view-content">
      <ListProjects v-if="currentView === 'caseManagement'" />
      <ProjectManagement v-else-if="currentView === 'projectManagement'" />
    </div>
    
    <!-- Small toggle switch in corner -->
    <div class="view-toggle-switch">
      <b-tooltip 
        :label="currentView === 'projectManagement' ? 'Switch to Case Management View' : 'Switch to Project Management View'"
        position="is-left"
        type="is-dark"
      >
        <button 
          class="toggle-button" 
          @click="toggleView"
          :class="{ 'is-case-view': currentView === 'caseManagement' }"
        >
          <i class="fas fa-exchange-alt"></i>
        </button>
      </b-tooltip>
    </div>
  </div>
</template>

<script>
import ListProjects from './ListProjects.vue';
import ProjectManagement from './ProjectManagement.vue';

export default {
  name: 'ProjectViewSwitcher',
  components: {
    ListProjects,
    ProjectManagement
  },
  data() {
    return {
      currentView: 'projectManagement' // Default view changed to projectManagement
    };
  },
  methods: {
    toggleView() {
      this.currentView = this.currentView === 'projectManagement' ? 'caseManagement' : 'projectManagement';
    }
  }
};
</script>

<style scoped lang="scss">
@import '@/assets/styles/dark-variables.scss';

.project-view-switcher {
  position: relative;
  height: 100%;
  
  .view-content {
    height: 100%;
  }
  
  .view-toggle-switch {
    position: fixed;
    bottom: 10px;
    left: 20px;
    z-index: 100;
    
    .toggle-button {
      background-color: $dark-bg-secondary;
      border: 1px solid $dark-border-color;
      color: $dark-text-primary;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s ease;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
      
      &:hover {
        background-color: $dark-bg-hover;
        transform: scale(1.1);
      }
      
      &.is-case-view {
        background-color: rgba($primary, 0.2);
        border-color: $primary;
        color: $primary;
      }
      
      .fa-exchange-alt {
        font-size: 14px;
        transform: rotate(90deg);
      }
    }
  }
}
</style>