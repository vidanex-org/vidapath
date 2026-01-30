<!-- Copyright (c) 2009-2022. Authors: see NOTICE file.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.-->

<template>
    <div class="magnification-selector">
        <div class="buttons has-addons are-small">
            <button class="button" @click="$emit('fit')">
                Fit
            </button>
            <button v-for="mag in magnifications" :key="mag" class="button"
                :class="{ 'is-selected': isCurrentMagnification(mag) }" @click="$emit('setMagnification', mag)">
                {{ mag }}X
            </button>
        </div>
    </div>
</template>

<script>
export default {
    name: 'magnification-selector',
    props: {
        image: Object,
        zoom: Number
    },
    data() {
        return {
            magnifications: [1.25, 2.5, 5, 10, 20, 40]
        };
    },
    computed: {
        currentMagnification() {
            if (!this.image || !this.image.magnification) return null;
            return Math.pow(2, this.zoom - this.image.zoom) * this.image.magnification;
        }
    },
    methods: {
        isCurrentMagnification(mag) {
            if (!this.currentMagnification) return false;
            return Math.abs(this.currentMagnification - mag) < 0.1;
        }
    }
};
</script>

<style scoped lang="scss">
@import '../../assets/styles/dark-variables';

.magnification-selector {
    position: absolute;
    left: 3.5rem;
    top: 3.5rem;
    z-index: 30;
    pointer-events: auto;
}

.buttons {
    margin-bottom: 0;
}

.button {
    background-color: $dark-bg-primary !important;
    color: $dark-text-primary !important;
    border: 1px solid $dark-border-color !important;
    margin-bottom: 0 !important;

    &:hover {
        background-color: $dark-bg-hover !important;
        color: $dark-text-primary !important;
    }

    &.is-selected {
        background-color: #6899d0 !important;
        color: $dark-text-primary !important;
        border-color: #6899d0 !important;
    }
}
</style>