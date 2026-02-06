import { Cytomine } from '@/api';

export default {
  namespaced: true,

  state: {
    easyImportEnableFolderBased: true, // Default value
    loaded: false,
    error: null
  },

  mutations: {
    SET_UI_CONFIG(state, config) {
      state.easyImportEnableFolderBased = config.easyImportEnableFolderBased;
      state.loaded = true;
      state.error = null;
    },

    SET_ERROR(state, error) {
      state.error = error;
      state.loaded = true;
    },

    resetState(state) {
      state.easyImportEnableFolderBased = true;
      state.loaded = false;
      state.error = null;
    }
  },

  actions: {
    async fetchServerConfig({commit}) {
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
    isFolderBasedEnabled: state => state.easyImportEnableFolderBased,
    isLoaded: state => state.loaded,
    hasError: state => state.error !== null
  }
};
