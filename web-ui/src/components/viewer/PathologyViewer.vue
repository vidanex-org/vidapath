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
        
        <!-- Custom panel for prostate-gleason -->
        <template v-if="result.runnerName === 'prostate-gleason'">
          <b-tabs v-model="result.activeTab" size="is-small" class="gleason-tabs" expanded>
            <!-- Annotations Tab -->
            <b-tab-item label="Annotations">
              <div class="gleason-section">
                <div class="level is-mobile mb-2">
                  <div class="level-left">
                    <label class="switch is-small">
                      <input type="checkbox" v-model="result.showAllAnnotations">
                      <span class="switch-slider"></span>
                    </label>
                    <span class="ml-2 is-size-7">Show results on image</span>
                  </div>
                  <div class="level-right">
                    <span class="is-size-7">%</span>
                  </div>
                </div>
                <!-- Annotation items -->
                <div class="item" v-for="anno in result.annotations" :key="anno.label">
                  <div class="left">
                    <label class="switch is-small">
                      <input type="checkbox" v-model="anno.showOnImage">
                      <span class="switch-slider"></span>
                    </label>
                    <span class="dot" :style="{ background: anno.color }"></span>
                    <span class="is-size-7 text-ellipsis" :title="anno.label">{{ anno.label }}</span>
                  </div>
                  <div class="right is-size-7">
                    <span v-if="anno.percent !== undefined">{{ anno.percent }}</span>
                    <span v-else-if="anno.present !== undefined">{{ anno.present ? 'Present' : 'Absent' }}</span>
                  </div>
                </div>
              </div>
            </b-tab-item>

            <!-- Areas Tab -->
            <b-tab-item label="Areas">
              <div class="gleason-section">
                <div class="is-size-7 mb-2 text-muted">Resolution: <strong>0.25 μm/px</strong></div>
                <!-- Area items -->
                <div class="item" v-for="area in result.areas" :key="area.label">
                  <div class="left">
                    <span class="dot" :style="{ background: area.color }"></span>
                    <span class="is-size-7">{{ area.label }}</span>
                  </div>
                  <div class="right is-size-7">{{ area.value }} mm²</div>
                </div>
                
                <div class="mt-4 is-size-7 has-text-weight-bold">Measurements</div>
                <div class="item">
                  <div class="left">
                    <label class="switch is-small">
                      <input type="checkbox" v-model="result.measurements.showTumorLength">
                      <span class="switch-slider"></span>
                    </label>
                    <span class="line-indicator" style="background: yellow;"></span>
                    <span class="is-size-7">Tumor length</span>
                  </div>
                  <div class="right is-size-7">{{ result.measurements.tumorLength }} mm</div>
                </div>
                <div class="item">
                  <div class="left">
                    <label class="switch is-small">
                      <input type="checkbox" v-model="result.measurements.showBiopsyLength">
                      <span class="switch-slider"></span>
                    </label>
                    <span class="line-indicator" style="background: #1E88E5;"></span>
                    <span class="is-size-7">Biopsy length</span>
                  </div>
                  <div class="right is-size-7">{{ result.measurements.biopsyLength }} mm</div>
                </div>
              </div>
            </b-tab-item>

            <!-- Scoring Tab -->
            <b-tab-item label="Scoring">
               <div class="gleason-section pt-2">
                  <div class="columns is-mobile is-multiline m-0">
                    <div class="column is-6 p-1">
                      <div class="box p-2 has-text-centered scoring-box">
                        <div class="is-size-7 has-text-grey">Primary</div>
                        <div class="is-size-5 has-text-weight-bold has-text-primary">{{ result.scoring.primaryPattern }}</div>
                      </div>
                    </div>
                    <div class="column is-6 p-1">
                      <div class="box p-2 has-text-centered scoring-box">
                        <div class="is-size-7 has-text-grey">Secondary</div>
                        <div class="is-size-5 has-text-weight-bold has-text-info">{{ result.scoring.secondaryPattern }}</div>
                      </div>
                    </div>
                    <div class="column is-12 p-1">
                      <div class="box p-2 has-text-centered scoring-box">
                        <div class="is-size-7 has-text-grey">Gleason Score</div>
                        <div class="is-size-4 has-text-weight-bold has-text-warning">{{ result.scoring.primaryPattern }} + {{ result.scoring.secondaryPattern }} = {{ result.scoring.totalScore }}</div>
                      </div>
                    </div>
                    <div class="column is-12 p-1">
                      <div class="box p-2 has-text-centered scoring-box">
                        <div class="is-size-7 has-text-grey">Grade Group</div>
                        <div class="is-size-4 has-text-weight-bold has-text-danger">{{ result.scoring.gradeGroup }}</div>
                      </div>
                    </div>
                  </div>
               </div>
            </b-tab-item>

            <!-- Report Tab -->
            <b-tab-item label="Report">
              <div class="gleason-section report-form">
                <div class="field is-horizontal is-small mb-2 align-items-center">
                  <div class="field-label is-small is-normal"><label class="label mb-0">Grade group</label></div>
                  <div class="field-body">
                    <div class="control">
                      <div class="select is-small is-fullwidth">
                        <select v-model="result.report.gradeGroup">
                          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="field is-horizontal is-small mb-2 align-items-center">
                  <div class="field-label is-small is-normal"><label class="label mb-0">Gleason</label></div>
                  <div class="field-body">
                    <div class="control">
                      <div class="select is-small is-fullwidth">
                        <select v-model="result.report.gleasonScore">
                          <option value="4+5">4 + 5 = 9</option>
                          <option value="3+4">3 + 4 = 7</option>
                          <option value="4+3">4 + 3 = 7</option>
                          <option value="3+3">3 + 3 = 6</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="field is-horizontal is-small mb-2 align-items-center" v-for="level in [5, 4, 3]" :key="'g'+level">
                  <div class="field-label is-small is-normal"><label class="label mb-0">Grade {{ level }} %</label></div>
                  <div class="field-body d-flex-row">
                    <div class="control" style="width:100%">
                      <input class="input is-small" type="number" step="0.1" v-model="result.report['gleason' + level]">
                    </div>
                  </div>
                </div>

                <div class="field is-horizontal is-small mb-2 align-items-center">
                  <div class="field-label is-small is-normal"><label class="label mb-0">Cribriform</label></div>
                  <div class="field-body">
                    <div class="control">
                      <div class="select is-small is-fullwidth">
                        <select v-model="result.report.cribriform">
                          <option value="Present">Present</option>
                          <option value="Absent">Absent</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>
                
                <hr class="my-2 has-background-grey-dark" />
                <div class="is-size-7 has-text-weight-bold mb-2">Tumor quantification</div>
                
                <div class="field is-horizontal is-small mb-2 align-items-center">
                  <div class="field-label is-small is-normal" style="flex-grow:2;"><label class="label mb-0">Tissue tumor %</label></div>
                  <div class="field-body d-flex-row">
                    <div class="control" style="width:100%">
                      <input class="input is-small" type="number" step="0.1" v-model="result.report.tumorQuantification">
                    </div>
                  </div>
                </div>
                
                <div class="field is-horizontal is-small mb-2 align-items-center">
                  <div class="field-label is-small is-normal" style="flex-grow:2;"><label class="label mb-0">Tumor len(mm)</label></div>
                  <div class="field-body d-flex-row">
                    <div class="control" style="width:100%">
                      <input class="input is-small" type="number" step="0.1" v-model="result.report.tumorLength">
                    </div>
                  </div>
                </div>

                <div class="field is-horizontal is-small mb-2 align-items-center">
                  <div class="field-label is-small is-normal" style="flex-grow:2;"><label class="label mb-0">Biopsy len(mm)</label></div>
                  <div class="field-body d-flex-row">
                    <div class="control" style="width:100%">
                      <input class="input is-small" type="number" step="0.1" v-model="result.report.biopsyLength">
                    </div>
                  </div>
                </div>

                <button class="button is-primary is-small is-fullwidth mt-3">CONFIRM RESULTS</button>
              </div>
            </b-tab-item>
          </b-tabs>
        </template>

        <!-- Standard AI result (if not prostate-gleason) -->
        <template v-else>
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
        </template>
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
        },
        // Mocking prostate-gleason AI result
        {
          id: 3,
          runnerName: 'prostate-gleason',
          visible: true,
          includeInReport: true,
          activeTab: 0,
          showAllAnnotations: true,
          annotations: [
            { label: "Benign", percent: 7.8, color: "#9575CD", showOnImage: false },
            { label: "Adenocarcinoma", percent: 4.6, color: "#E53935", showOnImage: false },
            { label: "Gleason 5", percent: 2.9, color: "#EF5350", showOnImage: false },
            { label: "Gleason 4", percent: 95.4, color: "#FFA726", showOnImage: false },
            { label: "Gleason 3", percent: 16.0, color: "#FFCA28", showOnImage: false },
            { label: "G4 cribriform", present: true, color: "#1E88E5", showOnImage: true },
            { label: "Perineural Invasion (PNI)", present: true, color: "#3949AB", showOnImage: true }
          ],
          areas: [
            { label: "Gleason 5", value: "2.1", color: "#EF5350" },
            { label: "Gleason 4", value: "85.2", color: "#FFA726" },
            { label: "Gleason 3", value: "1.4", color: "#FFCA28" },
            { label: "Total Tumor", value: "88.7", color: "#E53935" },
          ],
          measurements: {
            tumorLength: 31.4,
            biopsyLength: 57.7,
            showTumorLength: true,
            showBiopsyLength: true
          },
          scoring: {
            primaryPattern: 4,
            secondaryPattern: 5,
            totalScore: 9,
            gradeGroup: 5
          },
          report: {
            gradeGroup: 5,
            gleasonScore: '4+5',
            gleason5: 2.9,
            gleason4: 95.4,
            gleason3: 16.0,
            cribriform: 'Present',
            tumorQuantification: 54.4,
            tumorLength: 31.4,
            biopsyLength: 57.7
          }
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

/* Prostate Gleason Custom Styles */
.gleason-tabs {
  margin-top: 5px;
}
.gleason-tabs ::v-deep .tab-content {
  padding: 10px 5px !important;
}
.gleason-tabs ::v-deep .tabs li a {
  padding: 0.5em 0.8em;
  font-size: 0.8em;
}
.text-ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
  display: inline-block;
  vertical-align: middle;
}
.text-muted {
  color: #999;
}
.line-indicator {
  display: inline-block;
  width: 12px;
  height: 2px;
  margin-right: 6px;
}
.scoring-box {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}
.report-form .field-label {
  text-align: left;
  flex-grow: 1;
}
.report-form .field-body {
  flex-grow: 1;
  align-items: center;
  display: flex;
}
.align-items-center {
  align-items: center;
}
.d-flex-row {
  display: flex;
  flex-direction: row;
  align-items: center;
}
</style>