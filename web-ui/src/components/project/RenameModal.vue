<template>
  <cytomine-modal :active="active" title="Rename Item" @close="close">
    <div class="modal-form-content">
      <div class="form-section">
        <label class="form-label">New Name</label>
        <b-input 
          v-model="newName" 
          placeholder="Enter new name" 
          required
          ref="nameInput"
          @keyup.enter="renameItem"
        ></b-input>
        <p class="help-text">The name will be updated immediately after confirmation.</p>
      </div>
    </div>

    <template #footer>
      <button class="button is-outlined" type="button" @click="close">Cancel</button>
      <button 
        class="button is-primary" 
        @click="renameItem" 
        :disabled="!newName.trim() || newName === itemName"
        :loading="isRenaming"
      >
        Rename
      </button>
    </template>
  </cytomine-modal>
</template>

<script>
import CytomineModal from '../utils/CytomineModal.vue';

export default {
  name: 'RenameModal',
  components: {
    CytomineModal
  },
  props: {
    active: {
      type: Boolean,
      default: false
    },
    itemName: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      newName: '',
      isRenaming: false
    };
  },
  watch: {
    active(val) {
      if (val) {
        this.newName = this.itemName;
        this.isRenaming = false;
        this.$nextTick(() => {
          if (this.$refs.nameInput) {
            // Focus the input
            this.$refs.nameInput.focus();
            // Select all text in the input by accessing the underlying DOM element
            const inputElement = this.$refs.nameInput.$el.querySelector('input');
            if (inputElement) {
              inputElement.select();
            }
          }
        });
      }
    }
  },
  methods: {
    renameItem() {
      if (!this.newName.trim() || this.newName === this.itemName) return;
      
      this.isRenaming = true;
      this.$emit('rename', this.newName.trim());
      this.$emit('update:active', false);
    },
    close() {
      this.$emit('update:active', false);
    }
  }
};
</script>