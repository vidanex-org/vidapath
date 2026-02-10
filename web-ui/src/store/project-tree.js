import { ProjectCollection, ImageGroupCollection, ImageInstanceCollection, Project } from '@/api';

const state = {
  projects: [],
  imageGroupProjectMap: {},
  selectedItem: null,
  selectedItemType: null,
  selectedProject: null,
  all: true,
  searchString: '',
  // Content display state
  contentLoading: false,
  images: [],
  imageGroups: [],
};

const mutations = {
  SET_PROJECTS(state, projects) {
    state.projects = projects;
  },
  SET_IMAGE_GROUP_PROJECT_MAP(state, map) {
    state.imageGroupProjectMap = map;
  },
  SET_SELECTED_ITEM(state, { item, type }) {
    state.selectedItem = item;
    state.selectedItemType = type;
    if (type === 'project') {
      state.selectedProject = item;
    }
  },
  SET_SELECTED_PROJECT(state, project) {
    state.selectedProject = project;
  },
  SET_ALL_FILTER(state, all) {
    state.all = all;
  },
  SET_SEARCH_STRING(state, searchString) {
    state.searchString = searchString;
  },
  ADD_IMAGE_GROUP_TO_PROJECT(state, { project, imageGroup }) {
    const proj = state.projects.find(p => p.id === project.id);
    if (proj) {
      proj.imageGroups.push(imageGroup);
      proj.isExpanded = true;
    }
  },
  EXPAND_PROJECT(state, projectToExpand) {
    const project = state.projects.find(p => p.id === projectToExpand.id);
    if (project) {
      project.isExpanded = true;
    }
  },
  TOGGLE_PROJECT_EXPANSION(state, project) {
    const proj = state.projects.find(p => p.id === project.id);
    if (proj) {
      proj.isExpanded = !proj.isExpanded;
    }
  },
  // Content display mutations
  SET_CONTENT_LOADING(state, loading) {
    state.contentLoading = loading;
  },
  SET_CONTENT_DATA(state, { images, imageGroups }) {
    state.images = images;
    state.imageGroups = imageGroups;
  },
};

const actions = {
  async fetchProjects({ state, commit }) {
    try {
      const expandedProjectIds = state.projects
        .filter(p => p.isExpanded)
        .map(p => p.id);

      const projectCollection = new ProjectCollection({ all: state.all });
      const initialProjects = (await projectCollection.fetchAll()).array;

      let newProjects = [];
      let imageGroupProjectMap = {};

      for (const p of initialProjects) {
        const imageGroupCollection = new ImageGroupCollection({
          filterKey: 'project',
          filterValue: p.id
        });
        const fetchedImageGroups = (await imageGroupCollection.fetchAll()).array;
        
        fetchedImageGroups.forEach(ig => {
          imageGroupProjectMap[ig.id] = p.id;
        });
        
        newProjects.push({
          ...p,
          imageGroups: fetchedImageGroups,
          isExpanded: expandedProjectIds.includes(p.id)
        });
      }

      commit('SET_PROJECTS', newProjects);
      commit('SET_IMAGE_GROUP_PROJECT_MAP', imageGroupProjectMap);

      // Auto-select the first project if nothing is selected yet
      if (newProjects.length > 0 && !state.selectedItem) {
        commit('SET_SELECTED_ITEM', { item: newProjects[0], type: 'project' });
      }
    } catch (error) {
      console.error('Error fetching projects or image groups:', error);
    }
  },

  async fetchContent({ state, commit }) {
    commit('SET_CONTENT_LOADING', true);
    
    try {
      let images = [];
      let imageGroups = [];

      if (!state.selectedItem) {
        commit('SET_CONTENT_DATA', { images: [], imageGroups: [] });
        return;
      }

      if (state.selectedItemType === 'project') {
        // Fetch image groups for the project
        const imageGroupCollection = new ImageGroupCollection({
          filterKey: 'project',
          filterValue: state.selectedItem.id
        });
        const fetchedImageGroups = await imageGroupCollection.fetchAll();
        imageGroups = fetchedImageGroups.array;

        // Fetch images for the project (not belonging to any image group directly)
        const imageInstanceCollection = new ImageInstanceCollection({
          filterKey: 'project',
          filterValue: state.selectedItem.id
        });
        const fetchedImages = await imageInstanceCollection.fetchAll();
        images = fetchedImages.array.filter(image => !image.imageGroup);
      } else if (state.selectedItemType === 'imageGroup') {
        // Fetch images for the image group
        const imageInstanceCollection = new ImageInstanceCollection({
          filterKey: 'imagegroup',
          filterValue: state.selectedItem.id
        });
        const fetchedImages = await imageInstanceCollection.fetchAll();
        images = fetchedImages.array;
      }

      commit('SET_CONTENT_DATA', { images, imageGroups });
    } catch (error) {
      console.error('Error fetching content:', error);
      commit('SET_CONTENT_DATA', { images: [], imageGroups: [] });
    } finally {
      commit('SET_CONTENT_LOADING', false);
    }
  },

  async fetchProjectDetails({ state, commit }) {
    if (state.selectedItemType !== 'project' || !state.selectedItem) {
      return;
    }

    commit('SET_PROJECT_DETAILS_LOADING', true);
    try {
      // Fetch representatives
      const representatives = (await state.selectedItem.fetchRepresentatives()).array;
      // Fetch online users
      const onlines = await state.selectedItem.fetchConnectedUsers();
      
      commit('SET_PROJECT_DETAILS', { representatives, onlines });
    } catch (error) {
      console.error('Error fetching project details:', error);
      commit('SET_PROJECT_DETAILS', { representatives: [], onlines: [] });
    } finally {
      commit('SET_PROJECT_DETAILS_LOADING', false);
    }
  },

  setAllFilter({ commit, dispatch }, all) {
    commit('SET_ALL_FILTER', all);
    return dispatch('fetchProjects');
  },

  toggleProject({ commit }, project) {
    commit('TOGGLE_PROJECT_EXPANSION', project);
    commit('SET_SELECTED_ITEM', { item: project, type: 'project' });
  },

  selectImageGroup({ commit, state }, imageGroup) {
    const projectId = state.imageGroupProjectMap[imageGroup.id];
    const project = state.projects.find(p => p.id === projectId);
    if (project) {
      commit('EXPAND_PROJECT', project);
    }
    commit('SET_SELECTED_ITEM', { item: imageGroup, type: 'imageGroup' });
  },

  findProjectForImageGroup({ state }, imageGroup) {
    const projectId = state.imageGroupProjectMap[imageGroup.id];
    return state.projects.find(p => p.id === projectId);
  }
};

const getters = {
  filteredProjects: (state) => {
    if (!state.searchString || state.searchString.trim() === '') {
      return state.projects;
    }

    const searchLower = state.searchString.toLowerCase().trim();
    return state.projects.filter(project => {
      // Check if project name matches
      const projectMatches = project.name.toLowerCase().includes(searchLower);

      // Check if any image group matches
      const hasMatchingImageGroup = project.imageGroups.some(ig =>
        ig.name.toLowerCase().includes(searchLower)
      );

      // If either matches, include the project
      if (projectMatches || hasMatchingImageGroup) {
        // Auto-expand projects that have matches
        if (!project.isExpanded && hasMatchingImageGroup) {
          // This will be handled by the getter, but we need to ensure it's expanded
          // We'll handle this in the component instead of modifying state here
        }
        return true;
      }
      return false;
    });
  },

  getFilteredImageGroups: (state) => (imageGroups) => {
    if (!state.searchString || state.searchString.trim() === '') {
      return imageGroups;
    }

    const searchLower = state.searchString.toLowerCase().trim();
    return imageGroups.filter(ig =>
      ig.name.toLowerCase().includes(searchLower)
    );
  },
  
  // Content display getters
  contentLoading: (state) => state.contentLoading,
  contentImages: (state) => state.images,
  contentImageGroups: (state) => state.imageGroups,
  projectDetailsLoading: (state) => state.projectDetails.loading,
  projectRepresentatives: (state) => state.projectDetails.representatives,
  projectOnlines: (state) => state.projectDetails.onlines,
  
  // Helper getter to find project for image group
  findProjectForImageGroup: (state) => (imageGroup) => {
    const projectId = state.imageGroupProjectMap[imageGroup.id];
    return state.projects.find(p => p.id === projectId);
  }
};

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
};