<template>
  <div>
    <!-- Run Algorithm Controls -->
    <div class="panel">
      <div class="panel-title" @click="runAlgorithmPanelVisible = !runAlgorithmPanelVisible">
        <span>AI Analysis</span>
        <span class="arrow" :class="{ open: runAlgorithmPanelVisible }">▶</span>
      </div>
      <div v-if="runAlgorithmPanelVisible" class="panel-body ai-runner-selection">
        <div class="select is-fullwidth">
          <select v-model="selectedAIRunner" :disabled="loadingRunners">
            <option value="">Select AI Runner</option>
            <option v-for="runner in aiRunners" :key="runner.id" :value="runner">
              {{ runner.name }}
            </option>
          </select>
        </div>
        <button class="button is-primary" @click="runAlgorithm" :disabled="!selectedAIRunner || loadingRunners">
          <span class="icon is-small"><i class="fas fa-play"></i></span>
          <span>Run AI</span>
        </button>
      </div>
    </div>

    <!-- Dynamic AI Result Panels -->
    <div class="panel" v-for="result in aiResults" :key="result.id">
      <div class="panel-title" @click="result.visible = !result.visible">
        <div class="panel-title-left">
          <label class="switch" @click.stop>
            <input type="checkbox" v-model="result.includeInReport">
            <span class="switch-slider"></span>
          </label>
          <span class="panel-name">{{ result.runnerName }}</span>
        </div>
        <span class="arrow" :class="{ open: result.visible }">▶</span>
      </div>

      <div v-if="result.visible" class="panel-body">
        <h2 class="subtitle">AI Results</h2>
        <div class="item" v-for="item in result.stats" :key="item.label">
          <div class="left">
            <label class="switch is-small">
              <input type="checkbox" v-model="item.showOnImage">
              <span class="switch-slider"></span>
            </label>
            <span class="dot" :style="{ background: item.color }"></span>
            <span>{{ item.label }}</span>
          </div>
          <div class="right">
            <span>{{ item.count }}</span>
            <span v-if="item.percent !== null">{{ item.percent }}%</span>
          </div>
        </div>

        <h2 class="subtitle">Supplementary Terms</h2>
        <div class="supplementary-terms-list">
          <div class="item" v-for="termId in result.supplementaryTerms" :key="termId">
            <div class="left">
              <label class="switch is-small">
                <input type="checkbox" :checked="isResultTermVisible(termId)" @change="toggleResultTermVisibility(termId)">
                <span class="switch-slider"></span>
              </label>
              <span class="dot" :style="{ background: getTermColor(termId) }"></span>
              <span>{{ getTermName(termId) }}</span>
            </div>
            <div class="right">
              <button class="delete is-small" @click="removeSupplementaryTerm(result, termId)"></button>
            </div>
          </div>
          <div v-if="!result.supplementaryTerms || !result.supplementaryTerms.length" class="no-terms-notice">No supplementary terms added.</div>
        </div>
        <div class="supplementary-terms-controls">
          <button class="button is-small" @click.stop="toggleTermSelector(result.id)">
            {{ showTermSelectorFor === result.id ? 'Close' : 'Edit Terms' }}
          </button>
        </div>

        <ontology-tree
          v-if="showTermSelectorFor === result.id && treeReady"
          class="ontology-tree-container"
          v-model="result.supplementaryTerms"
          :ontologies="imageOntologies"
          :multiple="true"
        />

        <div class="grade">Overall grade for this result:
          <strong style="color: orange;">{{ result.grade }}</strong>
        </div>
      </div>
    </div>

        <!-- Manual Terms Panel -->
    <div class="panel">
      <div class="panel-title" @click="manualTermsPanelVisible = !manualTermsPanelVisible">
        <span>Manual Terms</span>
        <span class="arrow" :class="{ open: manualTermsPanelVisible }">▶</span>
      </div>
      <div v-if="manualTermsPanelVisible" class="panel-body">
        <div v-if="!hasOntologies" class="no-ontology-message">
          <p class="has-text-centered"><em>No terms</em></p>
          <p class="has-text-centered mt-2">
            <button class="button is-small is-link" @click="openSelectOntologyModal">Add terms</button>
          </p>
        </div>
        <div v-else>
          <div class="ontology-tags field is-grouped is-grouped-multiline mb-3">
            <div class="control" v-for="ontology in imageOntologies" :key="ontology.id">
              <div class="tags has-addons">
                <span class="tag is-info">{{ ontology.name }}</span>
                <a class="tag is-delete" @click="removeOntologyFromImage(ontology.id)" title="Remove ontology"></a>
              </div>
            </div>
          </div>

          <div class="ontology-tree-wrapper" v-if="treeReady">
            <div class="header-tree">
              <div class="sidebar-tree">
                <div class="visibility"><i class="far fa-eye"></i></div>
                <div class="opacity">Opacity</div>
              </div>
            </div>
            <ontology-tree :ontologies="imageOntologies" :allowSelection="false">
              <template #custom-sidebar="{ term }">
                <div class="sidebar-tree">
                  <div class="visibility">
                    <b-checkbox v-if="term.id" size="is-small" :value="getTermVisibility(term)" @input="toggleTermVisibility(term)"/>
                  </div>
                  <div class="opacity">
                    <input v-if="term.id" class="slider is-fullwidth is-small" step="0.05" min="0" max="1" type="range"
                      :value="getTermOpacity(term)" @change="event => changeOpacity(term, event)" @input="event => changeOpacity(term, event)">
                  </div>
                </div>
              </template>
            </ontology-tree>
          </div>
          <div v-else class="ontology-tree-loading">
            <i class="fas fa-spinner fa-spin"></i> Loading terms...
          </div>
          <div class="has-text-right mt-2">
            <button class="button is-small is-link" @click="openSelectOntologyModal">Add terms</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


<script>
import { AIRunner, AIAlgorithmJob } from '@/api';
import OntologyTree from '@/components/ontology/OntologyTree';

export default {
  components: {
    OntologyTree
  },
  props: {
    project: Object,
    index: String,
  },
  data() {
    return {
      // AI Runner相关数据
      aiRunners: [],
      selectedAIRunner: null,
      loadingRunners: true,
      runAlgorithmPanelVisible: true,
      manualTermsPanelVisible: true,
      treeReady: false, // 控制树组件的延迟渲染
      showTermSelectorFor: null,

      // Sample data structure for AI results
      aiResults: [
        {
          id: 1,
          runnerName: 'Mitosis Detector v1',
          visible: false,
          includeInReport: true,
          stats: [
            { label: "Mitosis", count: 200, percent: null, color: "#E53935", showOnImage: true },
          ],
          supplementaryTerms: [],
          grade: 'Grade 3'
        },
        {
          id: 2,
          runnerName: 'Tumor Segmentation v2',
          visible: false,
          includeInReport: true,
          stats: [
            { label: "Invasive carcinoma", count: 18.8, percent: 18.8, color: "#1E88E5", showOnImage: true },
            { label: "DCIS", count: "<0.5", percent: 0.5, color: "#00ACC1", showOnImage: false },
          ],
          supplementaryTerms: [],
          grade: 'Grade 2'
        }
      ],
    };
  },

  computed: {
    imageModule() {
      return this.$store.getters['currentProject/imageModule'](this.index);
    },
    imageWrapper() {
      return this.$store.getters['currentProject/currentViewer'].images[this.index];
    },
    imageOntologies() {
      return this.imageWrapper.ontologies || [];
    },
    hasOntologies() {
      return this.imageOntologies.length > 0;
    },
    ontologyTerms() {
      return this.imageWrapper.style.ontologyTerms;
    },
    allTerms() {
      return this.$store.getters[this.imageModule + 'terms'] || [];
    },
    termsMap() {
      const map = {};
      this.allTerms.forEach(term => {
        map[term.id] = term;
      });
      return map;
    },
    imageId() {
      return this.imageWrapper?.imageInstance?.id;
    }
  },
  methods: {
    async fetchAIRunners() {
      this.loadingRunners = true;
      try {
        this.aiRunners = await AIRunner.fetchAll();
      } catch (error) {
        console.error('Failed to fetch AI runners:', error);
        this.$buefy.toast.open({
          message: 'Failed to load AI runners',
          type: 'is-danger'
        });
      } finally {
        this.loadingRunners = false;
      }
    },

    runAlgorithm() {
      if (!this.selectedAIRunner) {
        this.$buefy.toast.open({
          message: 'Please select an AI runner',
          type: 'is-danger'
        });
        return;
      }

      this.$buefy.dialog.confirm({
        title: 'Confirm AI Processing',
        message: `Are you sure you want to run the AI algorithm "${this.selectedAIRunner.name}" on this image?`,
        type: 'is-primary',
        confirmText: 'Confirm',
        cancelText: 'Cancel',
        onConfirm: async () => {
          try {
            const requestData = {
              airunnerId: this.selectedAIRunner.id,
              projectId: parseInt(this.project.id),
              imageId: parseInt(this.imageId),
              // TODO: parameters field might be needed depending on the runner
            };

            await AIAlgorithmJob.runAlgorithm(requestData);

            this.$buefy.toast.open({
              message: 'AI processing started successfully',
              type: 'is-success'
            });

            // TODO: Poll for job status and add results to aiResults array

            this.selectedAIRunner = null;
          } catch (error) {
            this.$buefy.toast.open({
              message: 'Failed to start AI processing',
              type: 'is-danger'
            });
            console.error('AI processing failed:', error);
          }
        }
      });
    },

    openSelectOntologyModal() {
      this.$eventBus.$emit('openAddOntologyModal');
    },

    async removeOntologyFromImage(ontologyId) {
      if (!confirm('Are you sure you want to remove this ontology from the image?')) return;
      try {
        await this.$store.dispatch(this.imageModule + 'removeOntologyFromImage', ontologyId);
        this.$buefy.toast.open({ message: 'Ontology removed', type: 'is-success' });
      } catch (error) {
        console.log(error);
        this.$buefy.toast.open({ message: 'Error removing ontology', type: 'is-danger' });
      }
    },

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
      this.$store.commit(this.imageModule + 'toggleOntologyTermVisibility', { termId: term.id });
    },
    changeOpacity(term, event) {
      let opacity = Number(event.target.value);
      this.$store.commit(this.imageModule + 'setOntologyTermOpacity', { termId: term.id, opacity });
    },

    // Supplementary Terms Methods
    toggleTermSelector(resultId) {
      this.showTermSelectorFor = this.showTermSelectorFor === resultId ? null : resultId;
    },
    getTermName(termId) {
      const term = this.termsMap[termId];
      return term ? term.name : 'Unknown Term';
    },
    getTermColor(termId) {
      const term = this.termsMap[termId];
      return term ? term.color : '#000000';
    },
    isResultTermVisible(termId) {
      if (this.ontologyTerms && this.ontologyTerms[termId]) {
        return this.ontologyTerms[termId].visible;
      }
      return true;
    },
    toggleResultTermVisibility(termId) {
      this.$store.commit(this.imageModule + 'toggleOntologyTermVisibility', { termId });
    },
    removeSupplementaryTerm(result, termId) {
      result.supplementaryTerms = result.supplementaryTerms.filter(id => id !== termId);
    }
  },

  async mounted() {
    await this.fetchAIRunners();
    // 延迟渲染树组件，优先保证面板框架和动画的流畅性
    requestAnimationFrame(() => {
      this.treeReady = true;
    });
  }
};
</script>

<style scoped lang="scss">
@import '../../assets/styles/dark-variables';
@import '../../assets/styles/colors.scss';

.panel {
  width: 380px;
  border: 1px solid $dark-border-color;
  border-radius: 8px;
  background: $dark-bg-primary; // Applied to both for consistency
  color: $dark-text-primary;
}

.panel:not(:last-child) {
    margin-bottom: 5px;
}

@media (max-width: 768px) {
  .panel {
    width: 100%;
    border-radius: 0; /* Reset radius for full width look inside container */
    border: none;
  }
}

.panel-title {
  padding: 12px 14px;
  font-weight: bold;
  border-bottom: 1px solid $dark-border-color;
  display: flex;
  justify-content: space-between;
  cursor: pointer;
  background-color: $dark-bg-secondary;
  color: $dark-text-primary;
  align-items: center;
}

.panel-title-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-name {
  font-weight: bold;
}

.panel + .panel {
  margin-top: 2px;
}

.arrow {
  transition: 0.2s;
}

.arrow.open {
  transform: rotate(90deg);
}

.panel-body {
  padding: 10px 14px;
  background-color: $dark-bg-primary;
}

/* Switch */
.switch {
  position: relative;
  width: 42px;
  height: 22px;
  display: inline-block;
}

.switch input {
  display: none;
}

.switch-slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: $dark-bg-panel;
  border-radius: 20px;
  transition: 0.2s;
}

.switch-slider:before {
  content: "";
  position: absolute;
  width: 18px;
  height: 18px;
  left: 3px;
  bottom: 2px;
  background: $dark-text-secondary;
  border-radius: 50%;
  transition: 0.2s;
}

input:checked+.switch-slider {
  background: $primary;
}

input:checked+.switch-slider:before {
  transform: translateX(19px);
}

/* Small switch for item rows */
.switch.is-small {
  width: 34px;
  height: 18px;
}
.switch.is-small .switch-slider:before {
  width: 14px;
  height: 14px;
}
.switch.is-small input:checked+.switch-slider:before {
  transform: translateX(16px);
}

/* Items */
.item {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 14px;
  color: $dark-text-primary;
  border-bottom: 1px solid $dark-border-color;
}

.item:last-child {
  border-bottom: none;
}

.left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 6px;
}

.right {
  text-align: right;
  min-width: 60px;
}

.grade {
  margin-top: 4px;
  font-size: 14px;
  color: $dark-text-primary;
  padding: 4px 0;
}

.ai-runner-selection {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* Manual Terms Panel Styles */
.ontology-tree-wrapper {
  max-height: 17em;
  overflow: auto;
  margin-bottom: 0.4em !important;
}

.ontology-tree-loading {
  padding: 2em;
  text-align: center;
  color: $dark-text-secondary;
  font-style: italic;
}

.header-tree {
  display: flex;
  justify-content: right;
  position: sticky;
  top: 0;
  z-index: 5;
  padding-bottom: 0.3em;
  background: $dark-bg-primary;
  border-bottom: 1px solid $dark-border-color;
}

.sidebar-tree {
  padding-right: 0.4em;
  display: flex;
  align-items: center;
}

.visibility {
  width: 2.8em;
  display: flex;
  justify-content: center;
}

.opacity {
  width: 6em;
  text-align: center;
  font-size: 0.8em;
}

input[type="range"].slider {
  margin: 0;
  padding: 0;
}

::v-deep .checkbox .control-label {
  padding: 0 !important;
}

.no-ontology-message {
  padding: 1em;
  border: 1px dashed $dark-border-color;
  border-radius: 4px;
  margin-bottom: 1em;
}

.subtitle {
  font-size: 0.8em;
  color: $dark-text-secondary;
  text-transform: uppercase;
  margin-top: 15px;
  margin-bottom: 5px;
  font-weight: bold;
}

.supplementary-terms-controls {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.no-terms-notice {
  font-style: italic;
  color: $dark-text-disabled;
  font-size: 13px;
}

.ontology-tree-container {
  margin-top: 10px;
  border: 1px solid $dark-border-color;
  border-radius: 4px;
  padding: 5px;
}
</style>