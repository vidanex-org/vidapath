<template>
<div class="modal-card">
  <header class="modal-card-head">
    <p class="modal-card-title">{{title}}</p>
    <slot name="controls">
      <!-- 默认关闭按钮 -->
      <button class="delete" aria-label="close" @click="$emit('close')"></button>
    </slot>
  </header>
  <section class="modal-card-body">
    <slot></slot>
  </section>
  <footer class="modal-card-foot" v-if="footer">
    <slot name="footer">
      <button class="button" type="button" @click="$emit('close')">
        {{$t('button-close')}}
      </button>
    </slot>
  </footer>
</div>
</template>

<script>
export default {
  name: 'cytomine-modal-card',
  props: {
    title: String,
    footer: {type: Boolean, default: true}
  }
};
</script>

<style scoped lang="scss">
@import '../../assets/styles/dark-variables.scss';

.modal-card {
  background-color: $dark-bg-primary;
  color: $dark-text-primary;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.modal-card-head {
  background-color: $dark-bg-secondary;
  color: $dark-text-primary;
  border-bottom: 1px solid $dark-border-color;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-card-title {
  color: $dark-text-primary;
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.modal-card-body {
  background-color: $dark-bg-primary;
  color: $dark-text-primary;
  padding: 0.5rem;
  overflow-y: auto;
  overflow-x: hidden;
}

.modal-card-foot {
  background-color: $dark-bg-secondary;
  border-top: 1px solid $dark-border-color;
  padding: 1rem;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.button {
  background-color: $dark-button-bg;
  color: $dark-text-primary;
  border: 1px solid $dark-button-border;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.button:hover {
  background-color: $dark-button-hover-bg;
  border-color: $dark-button-hover-border;
}

.button:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

/* Delete button styles for dark theme */
.delete {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  background-color: transparent;
  border: none;
  cursor: pointer;
  display: inline-block;
  flex-shrink: 0;
  height: 20px;
  position: relative;
  vertical-align: top;
  width: 20px;
}

.delete::before,
.delete::after {
  background-color: $dark-text-primary;
  content: "";
  display: block;
  left: 50%;
  position: absolute;
  top: 50%;
  transform: translateX(-50%) translateY(-50%) rotate(45deg);
  transform-origin: center center;
}

.delete::before {
  height: 2px;
  width: 50%;
}

.delete::after {
  height: 50%;
  width: 2px;
}

.delete:hover::before,
.delete:hover::after {
  background-color: $dark-text-secondary;
}

.delete:focus {
  outline: none;
}
</style>