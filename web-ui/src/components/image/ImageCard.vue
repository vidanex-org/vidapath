<template>
  <div class="column is-one-fifth">
    <ImagePreview
      :image="image"
      :project="project"
      @show-details="openDrawer"
    />

    <ImageDetailsDrawer
      :active="showDrawer"
      :image="image"
      :editable="true"
      @close="showDrawer = false"
      @delete="handleDelete"
    />
  </div>
</template>

<script>
import ImagePreview from './ImagePreview.vue';
import ImageDetailsDrawer from './ImageDetailsDrawer.vue';

export default {
  name: 'ImageCard',
  components: {
    ImagePreview,
    ImageDetailsDrawer
  },
  props: {
    image: {
      type: Object,
      required: true
    },
    project: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      showDrawer: false
    };
  },
  methods: {
    async openDrawer() {
      // Ensure the project is set in the store before opening the drawer
      // ImageDetails component depends on currentProject/project from store
      if (this.project) {
        await this.$store.dispatch('currentProject/loadProject', this.project.id);
      }
      this.showDrawer = true;
    },
    handleDelete() {
      this.showDrawer = false;
      this.$emit('delete');
    }
  }
};
</script>