<template>
  <div v-show="show" class="context-menu" :style="{ top: top + 'px', left: left + 'px' }">
    <ul class="menu-list">
      <li v-for="(item, index) in items" :key="index">
        <a @click="itemClicked(item)">
          <span class="icon is-small" v-if="item.icon">
            <i :class="item.icon"></i>
          </span>
          <span>{{ item.label }}</span>
        </a>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'ContextMenu',
  props: {
    items: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      show: false,
      top: 0,
      left: 0
    };
  },
  methods: {
    open(event) {
      this.show = true;
      this.top = event.clientY;
      this.left = event.clientX;
      this.$nextTick(() => {
        this.$el.focus();
      });
    },
    close() {
      this.show = false;
    },
    itemClicked(item) {
      this.$emit('item-click', item);
      this.close();
    }
  }
};
</script>

<style scoped lang="scss">
@import '@/assets/styles/dark-variables.scss';

.context-menu {
  position: fixed;
  z-index: 1000;
  background-color: $dark-bg-secondary;
  border: 1px solid $dark-border-color;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
  padding: 0.5rem 0;

  .menu-list a {
    color: $dark-text-primary;
    padding: 0.5rem 1rem;
    display: flex;
    align-items: center;
    cursor: pointer;

    &:hover {
      background-color: $dark-bg-hover;
    }

    .icon {
      margin-right: 0.75rem;
    }
  }
}
</style>
