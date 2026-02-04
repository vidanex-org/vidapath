<template>
  <div class="project-view-switcher">
    <div class="field is-grouped is-grouped-centered">
      <p class="control">
        <b-button :type="currentView === 'caseManagement' ? 'is-primary' : ''" @click="currentView = 'caseManagement'">
          Case Management View
        </b-button>
      </p>
      <p class="control">
        <b-button :type="currentView === 'projectManagement' ? 'is-primary' : ''" @click="currentView = 'projectManagement'">
          Project Management View
        </b-button>
      </p>
    </div>

    <div class="view-content">
      <ListProjects v-if="currentView === 'caseManagement'" />
      <ProjectManagement v-else-if="currentView === 'projectManagement'" />
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
      currentView: 'caseManagement' // Default view
    };
  }
};
</script>

<style scoped>
.project-view-switcher {
  padding: 1rem;
}

.field.is-grouped.is-grouped-centered {
  margin-bottom: 1rem;
}
</style>
