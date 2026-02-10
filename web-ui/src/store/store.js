/*
* Copyright (c) 2009-2022. Authors: see NOTICE file.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*      http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

import Vue from 'vue';
import Vuex from 'vuex';

import appStores from './modules/app-stores.js';
import currentUser from './modules/current-user.js';
import currentProject from './modules/current-project.js';
import ontologies from './modules/ontologies.js';
import listProjects from './modules/list-projects.js';
import serverConfig from './modules/server-config.js';
import projectTree from './project-tree.js';

Vue.use(Vuex);
let store = new Vuex.Store({
  actions: {
    logout({state, commit}) {
      commit('appStores/reset');
      commit('currentUser/resetState');
      commit('currentProject/resetState');
      commit('ontologies/resetState');
      commit('listProjects/resetState');
      commit('serverConfig/resetState');
      commit('project-tree/SET_PROJECTS', []);
      commit('project-tree/SET_IMAGE_GROUP_PROJECT_MAP', {});
      commit('project-tree/SET_SELECTED_ITEM', { item: null, type: null });
      commit('project-tree/SET_SELECTED_PROJECT', null);
      for ( let key in state.projects) {
        this.unregisterModule(['projects', key]);
      }
    }
  },
  modules: {
    appStores,
    currentUser,
    currentProject,
    ontologies,
    listProjects,
    serverConfig,
    'project-tree': projectTree,
    projects: {
      namespaced: true
    }
  },
  strict: process.env.NODE_ENV !== 'production'
});

export default store;

export function getModuleNamespace(state) { // to update if https://github.com/vuejs/vuex/issues/1244 is implemented
  let pathes = Object.keys(store._modulesNamespaceMap);
  let moduleNamespace = pathes.find(path => store._modulesNamespaceMap[path].context.state === state);
  if (typeof moduleNamespace === 'string') {
    return moduleNamespace.slice(0, -1).split('/');
  }
}