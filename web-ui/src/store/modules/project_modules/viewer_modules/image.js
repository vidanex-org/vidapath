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

import {
  ImageInstance, AnnotationType, SliceInstanceCollection, SliceInstance,
  CompanionFileCollection, ImageGroupImageInstanceCollection, ImageGroup
} from '@/api';

import constants from '@/utils/constants';
import { slicePositionToRank } from '@/utils/slice-utils';
import { getAllTerms } from '@/utils/ontology-utils'; // 导入getAllTerms函数

import colors from './image_modules/colors';
import draw from './image_modules/draw';
import layers from './image_modules/layers';
import properties from './image_modules/properties';
import selectedFeatures from './image_modules/selected-features';
import style from './image_modules/style';
import tracking from './image_modules/tracking';
import undoRedo from './image_modules/undo-redo';
import view from './image_modules/view';
import review from './image_modules/review';
import tracks from './image_modules/tracks';
import annotationsList from './image_modules/annotations-list';
import controls from './image_modules/controls';

import _ from 'lodash';

import {
  isCluster,
  createTextStyle,
  selectStyles,
  verticesStyle,
  reviewedStyles,
  reviewedSelectStyles,
  rejectedStyles,
  rejectedSelectStyles,
  trackedSelectStyles,
  createColorStyle,
  createColorLineStyle
} from '@/utils/style-utils.js';
import { Fill } from 'ol/style';

function formatTerms(terms, layersOpacity, previousTerms = []) {
  if (!terms) {
    return;
  }

  let result = [];
  let nbTerms = terms.length;
  for (let i = 0; i < nbTerms; i++) {
    let term = terms[i];
    let prevTerm = previousTerms.find(prevTerm => prevTerm.id === term.id);
    result.push(prevTerm ? prevTerm : formatTerm(term, layersOpacity));
  }
  return result;
}

function formatTerm(term, layersOpacity) {
  let result = { id: term.id };
  result.opacity = 1;
  result.olStyle = createColorStyle(term.color, 1 * layersOpacity);
  result.olLineStyle = createColorLineStyle(term.color, 1 * layersOpacity);
  result.visible = true;
  result.color = term.color;
  return result;
}

export default {
  namespaced: true,

  state() {
    return {
      imageInstance: null,
      profile: null,
      imageGroupLink: null,
      imageGroup: null,
      sliceInstances: {},
      loadedSlicePages: [],
      activeSlices: null,
      activePanel: null,
      routedAnnotation: null,
      ontologies: [], // 存储图像关联的本体列表
      ontologyTerms: {} // 存储本体术语字典，键是本体ID，值是术语列表
    };
  },

  mutations: {
    setImageInstance(state, image) {
      state.imageInstance = image;
    },

    setResolution(state, resolution) {
      state.imageInstance.physicalSizeX = resolution.x;
      state.imageInstance.physicalSizeY = resolution.y;
      state.imageInstance.physicalSizeZ = resolution.z;
      state.imageInstance.fps = resolution.t;
    },

    togglePanel(state, panel) {
      state.activePanel = state.activePanel === panel ? null : panel;
    },

    clearSliceInstances(state) {
      state.sliceInstances = {};
      state.loadedSlicePages = [];
    },

    setSliceInstances(state, slices) {
      state.sliceInstances = Object.assign(
        {}, state.sliceInstances, slices.reduce((acc, v) => ({ ...acc, [v.rank]: v }), {})
      );
    },

    setLoadedSlicePage(state, page) {
      state.loadedSlicePages.push(page);
    },

    setActiveSlice(state, slice) {
      state.activeSlices = [slice];
    },

    setActiveSlices(state, slices) {
      state.activeSlices = slices;
    },

    setProfile(state, profile) {
      state.profile = profile;
    },

    setImageGroupLink(state, imageGroupLink) {
      state.imageGroupLink = imageGroupLink;
    },

    setImageGroup(state, imageGroup) {
      state.imageGroup = imageGroup;
    },

    setRoutedAnnotation(state, annotation) {
      state.routedAnnotation = annotation;
    },
    clearRoutedAnnotation(state) {
      state.routedAnnotation = null;
    },

    // 新增本体相关的mutations
    setOntologies(state, ontologies) {
      state.ontologies = ontologies;
    },

    addOntology(state, ontology) {
      if (!state.ontologies.find(ont => ont.id === ontology.id)) {
        state.ontologies.push(ontology);
      }
    },

    removeOntology(state, ontologyId) {
      state.ontologies = state.ontologies.filter(ont => ont.id !== ontologyId);
    },

    setStyleOntologyTerms(state, formattedOntologyTerms) {
      state.style.ontologyTerms = formattedOntologyTerms;
    },

    // 更新ontologyTerms的mutation
    updateOntologyTerms(state) {
      const newOntologyTerms = {};
      if (state.ontologies && Array.isArray(state.ontologies)) {
        for (const ontology of state.ontologies) {
          // 检查ontology对象是否有效，以及是否有children和array属性
          if (ontology && ontology.children && Array.isArray(ontology.children)) {
            const terms = getAllTerms(ontology);
            newOntologyTerms[ontology.id] = terms;
          } else {
            // 如果本体结构不完整，使用空数组作为terms
            newOntologyTerms[ontology.id] = [];
            console.warn('Ontology missing children or children.array property:', ontology);
          }
        }
      }
      state.ontologyTerms = newOntologyTerms;
    }
  },

  actions: {
    async initialize({ commit, dispatch, state }, { image, slices }) {
      let clone = image.clone();
      commit('setImageInstance', clone);

      clone = _.cloneDeep(slices);
      commit('setActiveSlices', clone);

      await Promise.all([
        dispatch('fetchProfile'),
        dispatch('fetchImageGroup'),
        dispatch('fetchSliceInstancesAround', { rank: clone[0].rank }),
      ]);
      commit('setOntologies', image.ontologies);
      console.log('image.ontologies', image.ontologies);
      commit('updateOntologyTerms'); // 使用mutation更新ontologyTerms

      // 更新style模块中的ontologyTerms
      const imageOntologyTerms = state.ontologyTerms;
      const formattedOntologyTerms = {};
      for (let ontologyId in imageOntologyTerms) {
        const terms = formatTerms(imageOntologyTerms[ontologyId], 0.5); // 使用默认的layersOpacity
        if (terms) {
          terms.forEach(term => {
            formattedOntologyTerms[term.id] = term;
          });
        }
      }

      console.log('formattedOntologyTerms', formattedOntologyTerms);
      commit('setStyleOntologyTerms', formattedOntologyTerms);
    },
    async setImageInstance({ dispatch, rootState }, { image, slices }) {
      await dispatch('initialize', { image, slices });
      let idProject = rootState.currentProject.project.id;
      let idViewer = rootState.currentProject.currentViewer;
      dispatch(`projects/${idProject}/viewers/${idViewer}/changePath`, null, { root: true });
    },

    async setActiveSlice({ commit, dispatch, rootState }, slice) {
      let idProject = rootState.currentProject.project.id;
      let idViewer = rootState.currentProject.currentViewer;
      commit('setActiveSlice', slice);
      dispatch(`projects/${idProject}/viewers/${idViewer}/changePath`, null, { root: true });
      await dispatch('fetchSliceInstancesAround', { rank: slice.rank });
    },
    async setActiveSliceByPosition({ state, dispatch }, { channel, zStack, time }) {
      let rank = slicePositionToRank({ channel, zStack, time }, state.imageInstance);
      await dispatch('setActiveSliceByRank', rank);
    },
    async setActiveSlicesByPosition({ state, dispatch }, { channels, zStack, time }) {
      let ranks = channels.map(channel => slicePositionToRank({ channel, zStack, time }, state.imageInstance));
      await dispatch('setActiveSlicesByRank', ranks);
    },
    async addActiveSliceChannel({ state, dispatch }, { channel }) {
      let activeSlice = state.activeSlices[0];
      let ranks = state.activeSlices.map(s => s.rank);
      ranks.push(slicePositionToRank({
        channel, zStack: activeSlice.zStack, time: activeSlice.time
      }, state.imageInstance));
      await dispatch('setActiveSlicesByRank', ranks);
    },
    async removeActiveSliceChannel({ state, dispatch }, { channel }) {
      let channels = state.activeSlices.map(s => s.channel).filter(c => c !== channel);
      let activeSlice = state.activeSlices[0];
      let ranks = channels.map(channel => slicePositionToRank({
        channel, zStack: activeSlice.zStack, time: activeSlice.time
      }, state.imageInstance));
      await dispatch('setActiveSlicesByRank', ranks);
    },
    async setActiveSliceByRank({ state, commit, dispatch, rootState }, rank) {
      let slice = state.sliceInstances[rank];
      if (!slice) {
        await dispatch('fetchSliceInstancesAround', { rank, setActive: true });
      } else {
        commit('setActiveSlice', slice);
      }

      let idProject = rootState.currentProject.project.id;
      let idViewer = rootState.currentProject.currentViewer;
      dispatch(`projects/${idProject}/viewers/${idViewer}/changePath`, null, { root: true });
    },
    async setActiveSlicesByRank({ state, commit, dispatch, rootState }, ranks) {
      let slices = await Promise.all(ranks.map(async rank => {
        let slice = state.sliceInstances[rank];
        if (!slice) {
          await dispatch('fetchSliceInstancesAround', { rank, setActive: false });
          slice = state.sliceInstances[rank];
        }
        return slice;
      }));
      commit('setActiveSlices', slices);

      let idProject = rootState.currentProject.project.id;
      let idViewer = rootState.currentProject.currentViewer;
      dispatch(`projects/${idProject}/viewers/${idViewer}/changePath`, null, { root: true });
    },

    async refreshData({ state, commit, dispatch }) {
      await Promise.all([
        ImageInstance.fetch(state.imageInstance.id).then(
          image => {
            commit('setImageInstance', image);
            commit('setOntologies', image.ontologies);
          }
        ),
        Promise.all(state.activeSlices.map(async slice => await SliceInstance.fetch(slice.id))).then(
          slices => commit('setActiveSlices', slices)
        )
      ]);

      commit('clearSliceInstances');

      await Promise.all([
        dispatch('fetchProfile'),
        dispatch('fetchImageGroup'),
        dispatch('fetchSliceInstancesAround', { rank: state.activeSlices[0].rank }),
      ]);

      commit('updateOntologyTerms');

      // 更新style模块中的ontologyTerms
      const imageOntologyTerms = state.ontologyTerms;
      const formattedOntologyTerms = {};
      for (let ontologyId in imageOntologyTerms) {
        const terms = formatTerms(imageOntologyTerms[ontologyId], 0.5); // 使用默认的layersOpacity
        if (terms) {
          terms.forEach(term => {
            formattedOntologyTerms[term.id] = term;
          });
        }
      }

      console.log('formattedOntologyTerms', formattedOntologyTerms);
      commit('setStyleOntologyTerms', formattedOntologyTerms);
    },

    async fetchProfile({ state, commit }) {
      let image = state.imageInstance;
      let profile = (await CompanionFileCollection.fetchAll({
        filterKey: 'abstractimage',
        filterValue: image.baseImage
      })).array.find(cf => cf.type === 'HDF5' && cf.status > 100);
      commit('setProfile', profile);
    },

    async fetchImageGroup({ state, commit }) {
      let image = state.imageInstance;
      let groupLinks = (await ImageGroupImageInstanceCollection.fetchAll({
        filterKey: 'imageinstance',
        filterValue: image.id
      })).array;
      let groupLink = (groupLinks.length > 0) ? groupLinks[0] : null;
      commit('setImageGroupLink', groupLink);

      if (groupLink) {
        let imageGroup = await ImageGroup.fetch(groupLink.group);
        commit('setImageGroup', imageGroup);
      }
    },

    async fetchSliceInstancesAround({ state, commit }, { rank, setActive = false }) {
      let promises = [];
      let props = { filterKey: 'imageinstance', filterValue: state.imageInstance.id, max: constants.PRELOADED_SLICES };

      let page = findRankPage(rank);
      if (!state.loadedSlicePages.includes(page)) {
        promises.push(new SliceInstanceCollection(props).fetchPage(page).then(data => {
          commit('setSliceInstances', data.array);
          if (setActive) {
            let active = data.array.find(slice => slice.rank === rank);
            if (active) {
              commit('setActiveSlice', active);
            }
          }
        }).then(() => commit('setLoadedSlicePage', page)));
      }

      let previous = page - 1;
      if (previous >= 0 && !state.loadedSlicePages.includes(previous)) {
        promises.push(new SliceInstanceCollection(props).fetchPage(previous).then(data => {
          commit('setSliceInstances', data.array);
        }).then(() => commit('setLoadedSlicePage', previous)));
      }

      let next = page + 1;
      if (next < findSliceInstanceNbPage(state.imageInstance) && !state.loadedSlicePages.includes(previous)) {
        promises.push(new SliceInstanceCollection(props).fetchPage(next).then(data => {
          commit('setSliceInstances', data.array);
        }).then(() => commit('setLoadedSlicePage', next)));
      }

      await Promise.all(promises);
    },

    async addOntologyToImage({ state, commit }, ontologyId) {
      if (!state.imageInstance || !state.imageInstance.id) {
        console.error('Cannot add ontology: no image instance or image ID');
        throw new Error('No image instance available');
      }

      try {
        const result = await state.imageInstance.addOntology(ontologyId);
        // 重新获取图像实例以获得包含完整术语树（children）的本体列表
        const image = await ImageInstance.fetch(state.imageInstance.id);
        commit('setOntologies', image.ontologies);
        commit('updateOntologyTerms'); // 使用mutation更新ontologyTerms

        // 更新style模块中的ontologyTerms
        const imageOntologyTerms = state.ontologyTerms;
        const formattedOntologyTerms = {};
        for (let ontologyId in imageOntologyTerms) {
          const terms = formatTerms(imageOntologyTerms[ontologyId], 0.5); // 使用默认的layersOpacity
          if (terms) {
            terms.forEach(term => {
              formattedOntologyTerms[term.id] = term;
            });
          }
        }

        console.log('formattedOntologyTerms', formattedOntologyTerms);
        commit('setStyleOntologyTerms', formattedOntologyTerms);

        return result;
      } catch (error) {
        console.error('Error adding ontology to image:', error);
        throw error;
      }
    },

    async removeOntologyFromImage({ state, commit }, ontologyId) {
      if (!state.imageInstance || !state.imageInstance.id) {
        console.error('Cannot remove ontology: no image instance or image ID');
        throw new Error('No image instance available');
      }

      try {
        const result = await state.imageInstance.removeOntology(ontologyId);
        // 从状态中移除本体
        commit('removeOntology', ontologyId);
        commit('updateOntologyTerms'); // 使用mutation更新ontologyTerms

        // 更新style模块中的ontologyTerms
        const imageOntologyTerms = state.ontologyTerms;
        const formattedOntologyTerms = {};
        for (let ontologyId in imageOntologyTerms) {
          const terms = formatTerms(imageOntologyTerms[ontologyId], 0.5); // 使用默认的layersOpacity
          if (terms) {
            terms.forEach(term => {
              formattedOntologyTerms[term.id] = term;
            });
          }
        }

        console.log('formattedOntologyTerms', formattedOntologyTerms);
        commit('setStyleOntologyTerms', formattedOntologyTerms);

        return result;
      } catch (error) {
        console.error('Error removing ontology from image:', error);
        throw error;
      }
    }
  },

  getters: {
    genStyleFunction: (state, getters) => (feature) => {
      let annot = feature.get('annot');
      if (!annot) {
        return;
      }

      // 添加对临时注释的特殊样式处理
      if (annot.isTemporary) {
        // 为临时注释添加虚线边框样式
        let tempStyle = state.style.defaultStyle.clone();
        let stroke = tempStyle.getStroke();
        if (stroke) {
          stroke.setLineDash([5, 5]); // 虚线样式
          stroke.setWidth(3);
        }
        let fill = tempStyle.getFill();
        if (fill) {
          // 降低填充透明度
          let color = fill.getColor();
          color[3] = 0.3; // 更透明
          fill.setColor(color);
        }

        let styles = [tempStyle];

        // 如果保存失败，添加特殊标识
        if (annot.saveFailed) {
          styles.push(createTextStyle('!', '22px', new Fill({ color: '#ff0000' }), null));
        }

        return styles;
      }

      // QUESTION: what to do with clusters (returned count does not take into account the selected terms) ?
      // Possible solutions:
      // 1. in backend, for clusters, send array with composition of cluster (x for term 1, y for term 2, z for term1-2)
      // 2. force source refresh every time the list of terms to display is updated
      // 3. add parameter allowing to provide the terms to take into account in kmeans (but only for kmeans)
      if (isCluster(feature)) {
        return [state.style.defaultStyle, createTextStyle(annot.count.toString())];
      }

      let styles = [];

      let nbTerms = annot.term.length;
      let ontologyTerms = state.style.ontologyTerms;

      if (ontologyTerms && nbTerms === 1) {
        let wrappedTerm = ontologyTerms[annot.term[0]];
        if (wrappedTerm) {
          if (!wrappedTerm.visible) {
            return; // do not display annot
          }
          if (feature.getGeometry().getType() === 'LineString') {
            styles.push(wrappedTerm.olLineStyle);
          } else {
            styles.push(wrappedTerm.olStyle);
          }
        } else {
          styles.push(state.style.noTermStyle); // could not find term => display no term style
        }
      } else if (ontologyTerms && nbTerms > 1) {
        // 遍历所有关联的本体，确保每个本体下至少有一个可见的术语被包含在注释中
        for (let ontology of state.ontologies) {
          // 检查该本体是否有术语在 annot.term 中，并且是可见的
          // 注意：如果注释中完全没有该本体的术语，这里逻辑上会被视为"不显示"（与原逻辑保持一致）
          // 原逻辑：ontologyTerms[ontoId].some(...)
          let rawTerms = state.ontologyTerms[ontology.id];
          if (rawTerms && rawTerms.length > 0) {
            // 检查 annot.term 中是否有属于该本体且可见的术语
            let hasTermsToDisplay = annot.term.some(termId => ontologyTerms[termId] && ontologyTerms[termId].ontology === ontology.id && ontologyTerms[termId].visible);
            if (!hasTermsToDisplay) {
              return; // do not display
            }
          }
        }
        styles.push(state.style.multipleTermsStyle);
      } else {
        if (!state.style.displayNoTerm) {
          return; // do not display annot
        }
        styles.push(state.style.noTermStyle);
      }

      let nbTracks = annot.track ? annot.track.length : 0;
      let isReviewed = annot.type === AnnotationType.REVIEWED;
      let isRejected = state.review.reviewMode && !isReviewed;

      // Styles for selected elements
      if (state.selectedFeatures.selectedFeatures.map(ftr => ftr.id).includes(feature.getId())) {
        styles.push(...(isReviewed ? reviewedSelectStyles : isRejected ? rejectedSelectStyles : (nbTracks > 0) ? trackedSelectStyles : selectStyles));

        // if in modify mode, display vertices
        if (state.draw.activeEditTool === 'modify') {
          styles.push(verticesStyle);
        }
      } else if (isReviewed) {
        styles.push(...reviewedStyles);
      } else if (isRejected) {
        styles.push(...rejectedStyles);
      }

      let tracks = state.style.wrappedTracks;

      if (tracks && nbTracks === 1) {
        let wrappedTrack = getters.tracksMapping[annot.track[0]];
        if (wrappedTrack) {
          if (feature.getGeometry().getType() === 'LineString') {
            styles.unshift(wrappedTrack.olLineStyle);
          } else {
            styles.push(wrappedTrack.olStyle);
          }
        }
      } else if (tracks && nbTracks > 1) {
        styles.push(state.style.multipleTracksStyle);
      }

      // Properties
      let propValue = state.properties.selectedPropertyValues[annot.id];
      if (propValue) {
        let color = state.properties.selectedPropertyColor;
        let fontSize = '34px';
        if (state.view.zoom <= 3) {
          fontSize = '12px';
        } else if (state.view.zoom <= 6) {
          fontSize = '19px';
        } else if (state.view.zoom <= 8) {
          fontSize = '26px';
        }
        styles.push(createTextStyle(propValue, fontSize, color.fill, null));
      }

      return styles;
    },

    maxZoom: state => {
      if (!state.imageInstance) {
        return 0;
      }
      let increment = state.view.digitalZoom ? constants.DIGITAL_ZOOM_INCREMENT : 0;
      return state.imageInstance.zoom + increment;
    },

    maxRank: state => {
      if (!state.imageInstance) {
        return 0;
      }

      return state.imageInstance.depth * state.imageInstance.duration * state.imageInstance.channels;
    },

    imageGroupId: state => {
      if (!state.imageGroupLink) {
        return null;
      }

      return state.imageGroupLink.group;
    },

    channels: state => {
      return _.orderBy(Object.values(_.groupBy(state.sliceInstances, 'channel')).map(slices => {
        return {
          index: slices[0].channel,
          name: slices[0].channelName,
          color: slices[0].channelColor
        };
      }), 'index');
    },

    hasOntologies: state => state.ontologies && state.ontologies.length > 0,

    ontologyById: state => id => state.ontologies.find(ont => ont.id === id),

    terms: (state) => {
      if (!state.ontologies || !Array.isArray(state.ontologies)) {
        return [];
      }

      let allTerms = [];
      for (const ontology of state.ontologies) {
        if (ontology && ontology.children && Array.isArray(ontology.children)) {
          const terms = getAllTerms(ontology);
          // 为每个term添加ontologyId属性
          const termsWithOntologyId = terms.map(term => ({
            ...term,
            ontologyId: ontology.id
          }));
          allTerms = allTerms.concat(termsWithOntologyId);
        }
      }
      console.log('allTerms:', allTerms);
      return allTerms;
    },

    ontologies: (state) => state.ontologies,
  },

  modules: {
    colors,
    draw,
    layers,
    properties,
    selectedFeatures,
    style,
    tracking,
    undoRedo,
    view,
    review,
    tracks,
    annotationsList,
    controls
  }
};

function findRankPage(rank) {
  return Math.ceil((rank + 1) / constants.PRELOADED_SLICES) - 1;
}

function findSliceInstanceNbPage(image) {
  return Math.ceil(image.depth * image.duration * image.channels / constants.PRELOADED_SLICES);
}
