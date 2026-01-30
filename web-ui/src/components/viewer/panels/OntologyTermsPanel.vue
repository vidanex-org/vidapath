<!-- Copyright (c) 2009-2022. Authors: see NOTICE file.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.-->

<template>
  <div class="ontology-terms-panel-container">
    <h1>Image {{ $t('terms') }}</h1>

    <!-- 当图像没有本体时显示此部分 -->
    <div v-if="!hasOntologies" class="no-ontology-message">
      <p class="has-text-centered">
        <em>No terms</em>
      </p>
      <p class="has-text-centered mt-2">
        <button class="button is-small is-link" @click="openSelectOntologyModal">
          Add terms
        </button>
      </p>
    </div>
    <!-- 当图像有本体或者用户无权限时显示正常的本体树 -->
    <div v-else class="ontology-panel">
      <div class="ontology-tags field is-grouped is-grouped-multiline mb-3">
        <div class="control" v-for="ontology in imageOntologies" :key="ontology.id">
          <div class="tags has-addons">
            <span class="tag is-info">{{ ontology.name }}</span>
            <a v-if="canManageProject" class="tag is-delete" @click="removeOntologyFromImage(ontology.id)"
               :title="$t('remove-ontology-from-image')"></a>
          </div>
        </div>
      </div>

      <div class="ontology-tree-wrapper">
        <div class="header-tree">
          <div class="sidebar-tree">
            <div class="visibility">
              <i class="far fa-eye"></i>
            </div>
            <div class="opacity">{{ $t('opacity') }}</div>
          </div>
        </div>
        <ontology-tree :ontologies="imageOntologies" :allowSelection="false">
          <template #custom-sidebar="{ term }">
            <div class="sidebar-tree">
              <div class="visibility">
                <b-checkbox v-if="term.id" size="is-small" :value="getTermVisibility(term)"
                            @input="toggleTermVisibility(term)"/>
                <b-checkbox v-else size="is-small" v-model="displayNoTerm"/>
              </div>

              <div class="opacity">
                <input v-if="term.id" class="slider is-fullwidth is-small" step="0.05" min="0" max="1" type="range"
                       :value="getTermOpacity(term)" @change="event => changeOpacity(term, event)"
                       @input="event => changeOpacity(term, event)">

                <input v-else class="slider is-fullwidth is-small" step="0.05" min="0" max="1" type="range"
                       v-model="noTermOpacity">
              </div>
            </div>
          </template>
        </ontology-tree>
      </div>
    </div>
    <div v-if="hasOntologies" class="has-text-right mt-2">
      <button class="button is-small is-link" @click="openSelectOntologyModal">
        Add terms
      </button>
    </div>
  </div>
</template>

<script>
import { get } from '@/utils/store-helpers';
import OntologyTree from '@/components/ontology/OntologyTree';

export default {
  name: 'ontology-terms-panel',
  components: { OntologyTree },
  props: {
    index: String
  },
  computed: {
    canManageProject() {
      return this.$store.getters['currentProject/canManageProject'];
    },
    imageModule() {
      return this.$store.getters['currentProject/imageModule'](this.index);
    },
    imageWrapper() {
      return this.$store.getters['currentProject/currentViewer'].images[this.index];
    },
    imageInstance() {
      return this.imageWrapper.imageInstance;
    },
    // 使用图像的本体而不是项目的本体
    imageOntologies() {
      return this.imageWrapper.ontologies || [];
    },
    hasOntologies() {
      return this.imageOntologies.length > 0;
    },

    ontologyTerms() {
      return this.imageWrapper.style.ontologyTerms;
    },
    additionalNodes() {
      return [{ id: 0, name: this.$t('no-term') }];
    },
    displayNoTerm: {
      get() {
        return this.imageWrapper.style.displayNoTerm;
      },
      set(value) {
        this.$store.dispatch(this.imageModule + 'setDisplayNoTerm', value);
      }
    },
    noTermOpacity: {
      get() {
        return this.imageWrapper.style.noTermOpacity;
      },
      set(value) {
        this.$store.commit(this.imageModule + 'setNoTermOpacity', Number(value));
      }
    },
  },
  watch: {
  },
  methods: {
    getTermVisibility(term) {
      if (this.ontologyTerms && this.ontologyTerms[term.id]) {
        return this.ontologyTerms[term.id].visible;
      }
      return true;
    },
    getTermOpacity(term) {
      if (this.ontologyTerms && this.ontologyTerms[term.id]) {
        return this.ontologyTerms[term.id].opacity;
      }
      return 0.5;
    },
    toggleTermVisibility(term) {
      // 注意：需要更新 style.js 中的 mutation 以支持直接传递 termId
      this.$store.commit(this.imageModule + 'toggleOntologyTermVisibility', { termId: term.id });
    },
    changeOpacity(term, event) {
      let opacity = Number(event.target.value);
      // 注意：需要更新 style.js 中的 mutation 以支持直接传递 termId
      this.$store.commit(this.imageModule + 'setOntologyTermOpacity', { termId: term.id, opacity });
    },
    resetOpacities() {
      this.$store.commit(this.imageModule + 'resetTermOpacities');
    },

    openSelectOntologyModal() {
      this.$eventBus.$emit('openAddOntologyModal');
    },

    async removeOntologyFromImage(ontologyId) {
      if (!confirm(this.$t('confirm-remove-ontology-from-image'))) return;

      try {
        // 调用store action从图像中移除本体
        await this.$store.dispatch(this.imageModule + 'removeOntologyFromImage', ontologyId);

        this.$notify({
          type: 'success',
          text: this.$t('notif-success-remove-ontology-from-image')
        });
      } catch (error) {
        console.log(error);
        this.$notify({
          type: 'error',
          text: this.$t('notif-error-remove-ontology-from-image')
        });
      }
    }
  }
};
</script>

<style scoped lang="scss">
@import '../../../assets/styles/dark-variables';

.ontology-terms-panel-container {
  width: 35em !important;
}

.ontology-panel {
  display: block;
  border: 1px solid $dark-border-color;
  border-radius: 4px;
  padding: 0.5em;
  width: 100%;
}

.ontology-tree-wrapper {
  max-height: 17em;
  overflow: auto;
  margin-bottom: 0.4em !important;
}

.no-ontology-message {
  padding: 1em;
  border: 1px dashed $dark-border-color;
  border-radius: 4px;
  margin-bottom: 1em;
}

input[type="range"].slider {
  margin: 0;
  padding: 0;
}

.header-tree {
  display: flex;
  justify-content: right;
  position: sticky;
  top: 0;
  z-index: 5;
  padding-bottom: 0.3em;
  background: transparent;
  border: 2px solid $dark-border-color;
  border-width: 0 0 2px !important;
}

.header-tree .opacity {
  text-align: center;
  text-transform: uppercase;
  font-size: 0.8em;
}

.sidebar-tree {
  padding-right: 0.4em;
  display: flex;
  align-items: center;
}

.visibility {
  width: 2.8em;
  height: 2.1em;
  display: flex;
  justify-content: center;
}

.header-tree .visibility {
  height: auto;
}

.opacity {
  width: 6em;
  display: block;
}

::v-deep .checkbox .control-label {
  padding: 0 !important;
}

::v-deep .ontology-tree .sl-vue-tree-node-item,
::v-deep .ontology-tree .no-result {
  line-height: 2;
  font-size: 0.9em;
}
</style>