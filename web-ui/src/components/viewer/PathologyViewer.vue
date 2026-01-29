<template>
  <div class="pathology-viewer dark-theme">
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
            <span class="slider"></span>
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
              <span class="slider"></span>
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
                <input type="checkbox" :checked="isTermVisible(result, termId)" @change="toggleTermVisibility(result, termId)">
                <span class="slider"></span>
              </label>
              <span class="dot" :style="{ background: getTermColor(termId) }"></span>
              <span>{{ getTermName(termId) }}</span>
            </div>
            <div class="right">
              <button class="delete is-small" @click="removeSupplementaryTerm(result, termId)"></button>
            </div>
          </div>
          <div v-if="!result.supplementaryTerms.length" class="no-terms-notice">No supplementary terms added.</div>
        </div>
        <div class="supplementary-terms-controls">
          <button class="button is-small" @click.stop="toggleTermSelector(result.id)">
            {{ showTermSelectorFor === result.id ? 'Close' : 'Edit Terms' }}
          </button>
        </div>

        <ontology-tree
          v-if="showTermSelectorFor === result.id"
          class="ontology-tree-container"
          v-model="result.supplementaryTerms"
          :ontologies="ontologies"
          :multiple="true"
        />

        <div class="grade">Overall grade for this result:
          <strong style="color: orange;">{{ result.grade }}</strong>
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
      showTermSelectorFor: null, // Tracks which panel's term selector is open

      // Sample data structure for AI results
      aiResults: [
        {
          id: 1,
          runnerName: 'Mitosis Detector v1',
          visible: true,
          includeInReport: true,
          stats: [
            { label: "Mitosis", count: 200, percent: null, color: "#E53935", showOnImage: true },
          ],
          supplementaryTerms: [],
          termVisibility: {},
          grade: 'Grade 3'
        },
        {
          id: 2,
          runnerName: 'Tumor Segmentation v2',
          visible: false,
          includeInReport: false,
          stats: [
            { label: "Invasive carcinoma", count: 18.8, percent: 18.8, color: "#1E88E5", showOnImage: true },
            { label: "DCIS", count: "<0.5", percent: 0.5, color: "#00ACC1", showOnImage: false },
          ],
          supplementaryTerms: [],
          termVisibility: {},
          grade: 'Grade 2'
        }
      ],
    };
  },

  computed: {
    imageModule() {
      return this.$store.getters['currentProject/imageModule'](this.index);
    },
    ontologies() {
      return this.$store.getters[this.imageModule + 'ontologies'];
    },
    allTerms() {
      return this.$store.getters[this.imageModule + 'terms'] || [];
    },
    imageId() {
      const imageWrapper = this.$store.getters['currentProject/currentViewer'].images[this.index];
      return imageWrapper?.imageInstance?.id;
    }
  },
  methods: {
    async fetchAIRunners() {
      this.loadingRunners = true;
      try {
        this.aiRunners = await AIRunner.fetchAll();
        console.log("Fetched AI runners:", this.aiRunners);
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

            console.log('Started AI processing with runner:', this.selectedAIRunner);

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

    toggleTermSelector(resultId) {
      if (this.showTermSelectorFor === resultId) {
        this.showTermSelectorFor = null; // Close if already open
      } else {
        this.showTermSelectorFor = resultId; // Open for this result
      }
    },

    getTermName(termId) {
      const term = this.allTerms.find(t => t.id === termId);
      return term ? term.name : 'Unknown Term';
    },

    getTermColor(termId) {
      const term = this.allTerms.find(t => t.id === termId);
      return term ? term.color : '#000000';
    },

    isTermVisible(result, termId) {
      if (!result.termVisibility) this.$set(result, 'termVisibility', {});
      return result.termVisibility[termId] !== false;
    },

    toggleTermVisibility(result, termId) {
      if (!result.termVisibility) this.$set(result, 'termVisibility', {});
      this.$set(result.termVisibility, termId, !this.isTermVisible(result, termId));
    },

    removeSupplementaryTerm(result, termId) {
      result.supplementaryTerms = result.supplementaryTerms.filter(id => id !== termId);
    }
  },

  async mounted() {
    await this.fetchAIRunners();
  }
};
</script>

<style scoped lang="scss">
@import '../../assets/styles/dark-variables';
@import '../../assets/styles/colors.scss';

.pathology-viewer.dark-theme {
  padding: 10px;
}

.panel {
  width: 380px;
  border: 1px solid $dark-border-color;
  border-radius: 8px;
  background: $dark-bg-primary; // Applied to both for consistency
  color: $dark-text-primary;
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
  margin-top: 10px;
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

.slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: $dark-bg-panel;
  border-radius: 20px;
  transition: 0.2s;
}

.slider:before {
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

input:checked+.slider {
  background: $primary;
}

input:checked+.slider:before {
  transform: translateX(19px);
}

/* Small switch for item rows */
.switch.is-small {
  width: 34px;
  height: 18px;
}
.switch.is-small .slider:before {
  width: 14px;
  height: 14px;
}
.switch.is-small input:checked+.slider:before {
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

.tags {
  flex-wrap: wrap;
  gap: 5px;
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

.ai-runner-selection {
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>