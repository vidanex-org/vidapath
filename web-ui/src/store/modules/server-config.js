import { Cytomine } from '@/api';

export default {
  namespaced: true,

  state: {
    easyImportProjectNameStrategy: 'folder', // Default value
    loaded: false,
    error: null
  },

  mutations: {
    SET_UI_CONFIG(state, config) {
      state.easyImportProjectNameStrategy = config.easyImportProjectNameStrategy;
      state.loaded = true;
      state.error = null;
    },

    SET_ERROR(state, error) {
      state.error = error;
      state.loaded = true;
    },

    resetState(state) {
      state.easyImportProjectNameStrategy = 'folder';
      state.loaded = false;
      state.error = null;
    }
  },

  actions: {
    async fetchServerConfig({ commit }) {
      try {
        const response = await Cytomine.instance.api.get('imageserver/ui-config.json');
        commit('SET_UI_CONFIG', response.data);
        return response.data;
      } catch (error) {
        console.error('Failed to fetch UI config:', error);
        commit('SET_ERROR', error.message);
        throw error;
      }
    }
  },

  getters: {
    isFolderBasedEnabled: state => state.easyImportProjectNameStrategy === 'folder' || state.easyImportProjectNameStrategy === 'pattern',
    isLoaded: state => state.loaded,
    hasError: state => state.error !== null
  }
};
