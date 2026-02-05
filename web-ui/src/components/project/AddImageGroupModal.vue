<template>
  <cytomine-modal :active="active" title="Create New Folder" @close="close">
    <div class="modal-form-content">
      <div class="form-section">
        <label class="form-label">Folder Name</label>
        <b-input 
          v-model="name" 
          placeholder="Enter a descriptive folder name" 
          required
          ref="nameInput"
          @keyup.enter="createImageGroup"
        ></b-input>
        <p class="help-text">Choose a clear and descriptive name for your folder.</p>
      </div>
    </div>

    <template #footer>
      <button class="button is-outlined" type="button" @click="close">Cancel</button>
      <button 
        class="button is-primary" 
        @click="createImageGroup" 
        :disabled="!name.trim()"
        :loading="isCreating"
      >
        Create Folder
      </button>
    </template>
  </cytomine-modal>
</template>

<script>
import CytomineModal from '../utils/CytomineModal.vue';

export default {
  name: 'AddImageGroupModal',
  components: {
    CytomineModal
  },
  props: {
    active: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      name: '',
      isCreating: false
    };
  },
  watch: {
    active(val) {
      if (val) {
        this.name = '';
        this.isCreating = false;
        this.$nextTick(() => {
          if (this.$refs.nameInput) {
            this.$refs.nameInput.focus();
          }
        });
      }
    }
  },
  methods: {
    createImageGroup() {
      if (!this.name.trim()) return;
      
      this.isCreating = true;
      this.$emit('create', this.name.trim());
      this.$emit('update:active', false);
    },
    close() {
      this.$emit('update:active', false);
    }
  }
};
</script>