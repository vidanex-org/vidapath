<template>
  <div class="image-details-drawer" :class="{ 'is-active': active }">
    <div class="drawer-background" @click="$emit('close')"></div>
    <div class="drawer-content">
      <div class="drawer-header">
        <h2 class="title is-4">
          <span class="icon">
            <i class="fas fa-image"></i>
          </span>
          <span>Image Details</span>
        </h2>
        <button class="delete" aria-label="close" @click="$emit('close')"></button>
      </div>
      <div class="drawer-body">
        <image-details
          v-if="image"
          :image="image"
          :editable="editable"
          :excludedProperties="excludedProperties"
          @delete="$emit('delete')"
        />
      </div>
    </div>
  </div>
</template>

<script>
import ImageDetails from './ImageDetails.vue';

export default {
  name: 'ImageDetailsDrawer',
  components: {
    ImageDetails
  },
  props: {
    active: {
      type: Boolean,
      default: false
    },
    image: {
      type: Object,
      default: null
    },
    editable: {
      type: Boolean,
      default: true
    },
    excludedProperties: {
      type: Array,
      default: () => [
        'metadata',
        'slide-preview',
        'numberOfReviewedAnnotations',
        'properties',
        'attached-files',
        'depth',
        'physicalSizeZ',
        'time',
        'fps',
        'channels'
      ]
    }
  },
  mounted() {
    this.hideUnwantedButtons();
  },
  updated() {
    this.hideUnwantedButtons();
  },
  methods: {
    hideUnwantedButtons() {
      // Hide unwanted action buttons using DOM manipulation
      this.$nextTick(() => {
        const buttons = this.$el.querySelectorAll('.image-details-wrapper .buttons .button');
        buttons.forEach(button => {
          const text = button.textContent.trim().toLowerCase();
          // Keep only Rename and Delete buttons
          if (!text.includes('rename') &&
              !text.includes('delete') &&
              !button.classList.contains('is-danger')) {
            button.style.display = 'none';
          }
        });
      });
    }
  }
};
</script>

<style lang="scss" scoped>
@import '../../assets/styles/dark-variables';

.image-details-drawer {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 50;
  display: none;
  overflow: hidden;
}

.image-details-drawer.is-active {
  display: flex;
}

.drawer-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  cursor: pointer;
}

.drawer-content {
  position: fixed;
  top: 0;
  right: 0;
  width: 600px;
  max-width: 90vw;
  height: auto;
  max-height: 90vh;
  background-color: $dark-bg-primary;
  display: flex;
  flex-direction: column;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.15);
  transform: translateX(100%);
  transition: transform 0.3s ease-out;
  color: $dark-text-primary;
  border-radius: 8px 0 0 8px;
  margin: 2rem 0;
}

.image-details-drawer.is-active .drawer-content {
  transform: translateX(0);
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid $dark-border-color;
  flex-shrink: 0;

  .title {
    color: $dark-text-primary;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;

    .icon {
      color: $primary;
    }
  }
}

.drawer-body {
  flex-grow: 1;
  overflow-y: auto;
  padding: 1.5rem;

  // Override image-details styles for drawer context
  ::v-deep .image-details-wrapper {
    .table {
      background-color: $dark-bg-primary;

      td {
        border-color: $dark-border-color;
      }

      .prop-label {
        background-color: $dark-bg-secondary;
        color: $dark-text-secondary;
      }

      .prop-content {
        background-color: $dark-bg-primary;
        color: $dark-text-primary;
      }
    }
  }
}

@media (max-width: 1024px) {
  .drawer-content {
    width: 90vw;
  }
}

@media (max-width: 768px) {
  .drawer-content {
    width: 95vw;
    margin: 1rem 0;
  }
}
</style>
