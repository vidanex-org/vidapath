<template>
  <cytomine-modal :active="active" title="Add Sub-folder" @close="close">
    <b-field label="Folder Name">
      <b-input v-model="name" placeholder="Enter folder name" required></b-input>
    </b-field>

    <template #footer>
      <button class="button" type="button" @click="close">Cancel</button>
      <button class="button is-primary" @click="createImageGroup" :disabled="!name">Save</button>
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
      name: ''
    };
  },
  watch: {
    active(val) {
      console.log('AddImageGroupModal active changed to:', val);
      if (val) {
        this.name = '';
      }
    }
  },
  methods: {
    createImageGroup() {
      this.$emit('create', this.name);
      this.$emit('update:active', false);
    },
    close() {
      this.$emit('update:active', false);
    }
  }
};
</script>
