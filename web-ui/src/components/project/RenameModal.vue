<template>
  <cytomine-modal :active="active" title="Rename" @close="close">
    <b-field label="New Name">
      <b-input v-model="newName" :placeholder="`Enter new name for ${itemName}`" required></b-input>
    </b-field>

    <template #footer>
      <button class="button" type="button" @click="close">Cancel</button>
      <button class="button is-primary" @click="renameItem" :disabled="!newName">Save</button>
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
      newName: ''
    };
  },
  watch: {
    active(val) {
      console.log('RenameModal active changed to:', val);
      if (val) {
        this.newName = '';
      }
    }
  },
  methods: {
    renameItem() {
      this.$emit('rename', this.newName);
      this.$emit('update:active', false);
    },
    close() {
      this.$emit('update:active', false);
    }
  }
};
</script>
