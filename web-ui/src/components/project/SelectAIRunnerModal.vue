<template>
  <cytomine-modal :active.sync="localActive" :title="$t('select-ai-models')" @close="handleClose">
    <p>{{ $t('please-select-an-ai-model-to-execute-this-case') }}</p>

    <div class="field">
      <div class="control">
        <div class="select is-fullwidth">
          <select v-model="selectedRunner">
            <option value="">{{ $t('please-select') }}</option>
            <option v-for="runner in aiRunners" :key="runner.id" :value="runner">
              {{ runner.name }} ({{ runner.runnerName }})
            </option>
          </select>
        </div>
      </div>
    </div>

    <template #footer>
      <button class="button" @click="handleClose">{{ $t('button-cancel') }}</button>
      <button class="button is-primary" :disabled="!selectedRunner" @click="handleConfirm">
        {{ $t('button-confirm') }}
      </button>
    </template>
  </cytomine-modal>
</template>

<script>
import CytomineModal from '@/components/utils/CytomineModal';
import { AIRunner } from '@/api';

export default {
  name: 'SelectAIRunnerModal',
  components: {
    CytomineModal
  },
  props: {
    active: {
      type: Boolean,
      default: false
    },
    aiRunners: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      selectedRunner: null
    };
  },
  computed: {
    localActive: {
      get() {
        return this.active;
      },
      set(value) {
        this.$emit('update:active', value);
      }
    }
  },
  watch: {
    active(newVal) {
      if (!newVal) {
        // 当模态框关闭时，重置选择
        this.selectedRunner = null;
      }
    }
  },
  methods: {
    handleClose() {
      this.$emit('update:active', false);
    },
    handleConfirm() {
      if (!this.selectedRunner) {
        this.$buefy.toast.open({
          message: this.$t('please-select-an-ai-runner'),
          type: 'is-danger'
        });
        return;
      }
      
      this.$emit('confirm', this.selectedRunner);
      this.$emit('update:active', false);
    }
  }
};
</script>

<style scoped lang="scss">
@import '@/assets/styles/dark-variables.scss';

.field {
  margin-top: 1rem;
}
</style>