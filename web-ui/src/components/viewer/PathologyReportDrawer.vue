<template>
  <div class="pathology-report-drawer" :class="{ 'is-active': active }">
    <div class="drawer-background"></div>
    <div class="drawer-content">
      <div class="drawer-header">
        <h2 class="title is-4">Histopathological Examination Report</h2>
        <button class="delete" aria-label="close" @click="$emit('close')"></button>
      </div>
      <div class="drawer-body">
        <div class="field">
          <label class="label">Clinical History</label>
          <div class="control">
            <textarea class="textarea" rows="2" v-model="report.clinicalHistory" :maxlength="10000"></textarea>
            <p class="help has-text-right">{{ report.clinicalHistory.length }} / 10000</p>
          </div>
        </div>

        <div class="field">
          <label class="label">Specimen Labelled As</label>
          <div class="control">
            <textarea class="textarea" rows="2" v-model="report.specimenLabel" :maxlength="10000"></textarea>
            <p class="help has-text-right">{{ report.specimenLabel.length }} / 10000</p>
          </div>
        </div>

        <div class="field">
          <label class="label">Grossed By</label>
          <div class="control">
            <textarea class="textarea" rows="4" v-model="report.grossedBy" :maxlength="15000"></textarea>
            <p class="help has-text-right">{{ report.grossedBy.length }} / 15000</p>
          </div>
        </div>

        <div class="field">
          <label class="label">Macroscopic</label>
          <div class="control">
            <textarea class="textarea" rows="4" v-model="report.macroscopic" :maxlength="15000"></textarea>
            <p class="help has-text-right">{{ report.macroscopic.length }}  / 15000</p>
          </div>
        </div>

        <div class="field">
          <label class="label">Microscopic</label>
          <div class="control">
            <textarea class="textarea" rows="4" v-model="report.microscopic" :maxlength="15000"></textarea>
            <p class="help has-text-right">{{ report.microscopic.length }} / 15000</p>
          </div>
        </div>

        <div class="field">
          <label class="label">Diagnosis</label>
          <div class="control">
            <textarea class="textarea" rows="4" v-model="report.Diagnosis" :maxlength="15000"></textarea>
            <p class="help has-text-right">{{ report.Diagnosis.length }} / 15000</p>
          </div>
        </div>
      </div>
      <div class="drawer-footer">
        <button class="button is-success">Save</button>
        <button class="button" @click="$emit('close')">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PathologyReportDrawer',
  props: {
    active: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      report: {
        clinicalHistory: '',
        specimenLabel: '',
        grossedBy: '',
        macroscopic: '',
        microscopic: '',
        Diagnosis: '',
      }
    };
  }
};
</script>

<style lang="scss" scoped>
@import '../../assets/styles/dark-variables';

.pathology-report-drawer {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 40;
  display: none;
  overflow-y: auto;
}

.pathology-report-drawer.is-active {
  display: flex;
}

.drawer-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
}

.drawer-content {
  position: fixed;
  top: 0;
  right: 0;
  width: 40vw;
  max-width: 90vw;
  height: 100%;
  background-color: $dark-bg-primary; /* Use dark theme background */
  display: flex;
  flex-direction: column;
  box-shadow: -2px 0 8px rgba(0,0,0,0.15);
  transform: translateX(100%);
  transition: transform 0.3s ease-out;
  color: $dark-text-primary; /* Set default text color */
}

.pathology-report-drawer.is-active .drawer-content {
    transform: translateX(0);
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid $dark-border-color; /* Use dark theme border color */
}

.drawer-header .title {
  color: $dark-text-primary; /* Ensure title color is consistent */
}

.drawer-body {
  flex-grow: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  padding: 1rem 1.5rem;
  border-top: 1px solid $dark-border-color; /* Use dark theme border color */
}

.drawer-footer .button {
  margin-left: 0.5rem;
}

.textarea, .input {
  background-color: $dark-bg-secondary; /* Lighter background for inputs */
  border-color: $dark-border-color;
  color: $dark-text-primary;
}

.textarea::placeholder, .input::placeholder {
  color: $dark-text-secondary;
}

.label {
  color: $dark-text-primary; /* Label text color */
}

.help {
  color: $dark-text-secondary; /* Help text color */
}
</style>
