<template>
  <div class="column is-one-quarter">
    <ImagePreview :image="image" :project="project" />
  </div>
</template>

<script>
import ImagePreview from './ImagePreview.vue';

export default {
  name: 'ImageCard',
  components: {
    ImagePreview
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
  }
};
</script>
