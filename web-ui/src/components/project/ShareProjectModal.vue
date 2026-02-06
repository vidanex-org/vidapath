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
  <cytomine-modal :active="active" :title="modalTitle" @close="$emit('update:active', false)">
    <b-loading :is-full-page="false" :active="loading" />
    <div v-if="!loading" class="share-project-modal">
      <div v-if="shareType === 'public'" class="form-section element-spacing">
        <!-- 添加过期时间选项 -->
        <div class="form-section element-spacing">
          <b-field :label="'Expiration time'" class="field-spacing">
            <b-select v-model="expirationTime" expanded>
              <option value="5">In 5 hours</option>
              <option value="24">In 1 day</option>
              <option value="72">In 3 days</option>
              <option value="168">In 1 week</option>
              <option value="720">In 1 month</option>
            </b-select>
          </b-field>
        </div>
      </div>

      <div class="share-link element-spacing" v-if="generatedLink">
        <b-field :label="'Share link'" class="field-spacing">
          <b-input v-model="generatedLink" readonly expanded class="share-link-input" />
          <p class="control">
            <button class="button is-link" @click="copyLink">Copy</button>
          </p>
        </b-field>
      </div>

      <div class="bulk-share-info element-spacing" v-if="isBulkShare">
        <b-message type="is-info" has-icon>
          Sharing {{ projects.length }} case(s) with the same link.
        </b-message>
      </div>
    </div>

    <template #footer>
      <button class="button" @click="$emit('update:active', false)">
        Cancel
      </button>
      <button class="button is-primary" @click="shareProject" :disabled="loading">
        Share
      </button>
    </template>
  </cytomine-modal>
</template>

<script>
import CytomineModal from '@/components/utils/CytomineModal';
import { UserCollection, Project, Cytomine, ImageInstanceCollection } from '@/api';

export default {
  name: 'share-project-modal',
  props: {
    active: Boolean,
    project: Object, // 单个项目分享时使用
    projects: Array  // 批量项目分享时使用
  },
  components: {
    CytomineModal
  },
  data() {
    return {
      loading: false,
      shareType: 'public', // 'public' or 'users'
      expirationTime: '24', // 过期时间选项
      generatedLink: ''
    };
  },
  computed: {
    isBulkShare() {
      return this.projects && this.projects.length > 0;
    },
    modalTitle() {
      return this.isBulkShare ? 'Bulk Share Projects' : 'Share Project';
    }
  },
  watch: {
    active(val) {
      if (val) {
        this.resetForm();
      } else {
        this.generatedLink = '';
      }
    }
  },
  methods: {
    resetForm() {
      this.shareType = 'public';
      this.expirationTime = '24';
      this.generatedLink = '';
    },

    async shareProject() {
      this.loading = true;
      try {
        if (this.isBulkShare) {
          await this.shareMultipleProjects();
        } else {
          await this.shareSingleProject();
        }
      } catch (error) {
        console.error('Error sharing project(s):', error);
        this.$notify({ type: 'error', text: 'Failed to share project(s).' });
      } finally {
        this.loading = false;
      }
    },

    async shareSingleProject() {
      // 获取项目的第一张图像
      const firstImage = await this.getFirstImage(this.project.id);
      if (!firstImage) {
        this.$notify({ type: 'error', text: 'No images found in this project. Cannot generate share link.' });
        return;
      }

      // 生成临时访问令牌
      await this.generateTokenAndLink([this.project.id]);
    },

    async shareMultipleProjects() {
      // 获取所有项目中第一张图像
      const projectIds = this.projects.map(p => p.id);

      // 生成临时访问令牌，包含所有项目ID
      await this.generateTokenAndLink(projectIds);
    },

    async getFirstImage(projectId) {
      try {
        const imageCollection = new ImageInstanceCollection({
          filterKey: 'project',
          filterValue: projectId,
          sort: 'id',
          order: 'asc',
          max: 1
        });

        const images = await imageCollection.fetchPage(0);
        return images.array.length > 0 ? images.array[0] : null;
      } catch (error) {
        console.error('Error fetching images:', error);
        return null;
      }
    },

    async generateTokenAndLink(projectIds) {
      try {
        // 调用后端API生成临时访问令牌，支持多个项目ID
        const response = await Cytomine.instance.api.post('/temporary_access_token.json', {
          expirationHours: parseInt(this.expirationTime),
          projectId: projectIds
        });
        const token = response.data.tokenKey;


        if (this.isBulkShare) {
          this.generatedLink = `${window.location.origin}/#/projects?access_token=${token}`;
        } else {
          // 使用项目的ID和第一张图像生成链接
          const firstProjectId = projectIds[0];
          const firstImage = await this.getFirstImage(firstProjectId);
          this.generatedLink = `${window.location.origin}/#/project/${firstProjectId}/image/${firstImage.id}?access_token=${token}`;
        }

        // 自动复制链接到剪贴板
        this.copyToClipboard(this.generatedLink).then(() => {
          this.$notify({ type: 'success', text: 'Link copied to clipboard.' });
        }).catch(err => {
          console.error('Failed to copy: ', err);
          this.$notify({ type: 'error', text: 'Failed to copy link.' });
        });
      } catch (error) {
        console.error('Error generating temporary access token:', error);
        this.$notify({ type: 'error', text: 'Failed to generate temporary access token.' });
      }
    },

    copyLink() {
      this.copyToClipboard(this.generatedLink).then(() => {
        this.$notify({ type: 'success', text: 'Link copied to clipboard.' });
      }).catch(err => {
        console.error('Failed to copy: ', err);
        this.$notify({ type: 'error', text: 'Failed to copy link.' });
      });
    },
    
    copyToClipboard(text) {
      // 检查浏览器是否支持 navigator.clipboard
      if (!navigator.clipboard && window.isSecureContext) {
        // 使用现代 Clipboard API
        return navigator.clipboard.writeText(text);
      } else {
        // 回退到传统的 document.execCommand 方法
        return this.fallbackCopyTextToClipboard(text);
      }
    },
    
    fallbackCopyTextToClipboard(text) {
      // 创建一个 textarea 元素用于复制文本
      const textArea = document.createElement("textarea");
      textArea.value = text;
      
      // 避免滚动到底部
      textArea.setAttribute("readonly", "");
      textArea.style.cssText = `
        position: absolute;
        left: -9999px;
        top: -9999px;
        opacity: 0;
        height: 0;
        width: 0;
        overflow: hidden;
      `;
      
      document.body.appendChild(textArea);
      textArea.select();
      
      return new Promise((resolve, reject) => {
        let success = false;
        try {
          // 执行复制命令
          success = document.execCommand('copy');
        } catch (err) {
          console.error('Fallback: Could not copy text: ', err);
        }
        
        document.body.removeChild(textArea);
        
        if (success) {
          resolve();
        } else {
          // 如果复制失败，提供错误信息
          reject(new Error('Could not copy text'));
        }
      });
    }
  }
};
</script>

<style scoped lang="scss">
@import '../../assets/styles/dark-variables';

.share-project-modal {
  padding: 1.5rem;
}

.form-section {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid $dark-border-color;
}

.form-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.element-spacing {
  margin-bottom: 1.25rem;
}

.field-spacing {
  margin-bottom: 1rem;
}

.field-label {
  font-weight: 600;
  color: $dark-text-primary;
  margin-bottom: 0.5rem;
}

.share-link {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid $dark-border-color;
}

.share-link-input {
  background-color: #2d2d2d !important;
  color: $dark-text-primary;
  border-color: $dark-input-border;
}

.input[readonly] {
  background-color: #2d2d2d !important;
}

.share-link-input::placeholder {
  color: $dark-text-disabled;
}

.share-link-input:focus {
  border-color: $dark-input-focus-border;
  box-shadow: 0 0 0 0.2rem $dark-input-focus-shadow;
}

/* 暗黑模式下的消息框样式 */
:deep(.message) {
  background-color: $dark-bg-secondary;
  color: $dark-text-primary;
  border-color: $dark-border-color;
}

:deep(.message.is-info) {
  background-color: rgba(64, 158, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.5);
}

:deep(.message.is-warning) {
  background-color: rgba(255, 193, 7, 0.1);
  border-color: rgba(255, 193, 7, 0.5);
}

/* 暗黑模式下的单选按钮样式 */
:deep(.radio) {
  color: $dark-text-primary;
}

:deep(.radio input[type="radio"]) {
  background-color: $dark-input-bg;
  border-color: $dark-input-border;
}

:deep(.radio input[type="radio"]:checked) {
  background-color: $dark-button-bg;
  border-color: $dark-button-border;
}

/* 暗黑模式下的选择框样式 */
:deep(.select) {
  width: 100%;
}

:deep(.select select) {
  background-color: $dark-input-bg;
  color: $dark-text-primary;
  border-color: $dark-input-border;
}

:deep(.select select:focus) {
  border-color: $dark-input-focus-border;
  box-shadow: 0 0 0 0.2rem $dark-input-focus-shadow;
}

:deep(.select:not(.is-multiple):not(.is-loading)::after) {
  border-color: $dark-text-primary;
}

/* 暗黑模式下的标签输入框样式 */
:deep(.taginput) {
  background-color: $dark-input-bg;
  border-color: $dark-input-border;
}

:deep(.taginput-container) {
  background-color: $dark-input-bg;
  color: $dark-text-primary;
}

:deep(.taginput-container .tag) {
  background-color: $dark-button-bg;
  color: $dark-text-primary;
}

/* 暗黑模式下的输入框样式 */
:deep(.input) {
  background-color: $dark-input-bg;
  color: $dark-text-primary;
  border-color: $dark-input-border;
}

:deep(.input::placeholder) {
  color: $dark-text-disabled;
}

:deep(.input:focus) {
  border-color: $dark-input-focus-border;
  box-shadow: 0 0 0 0.2rem $dark-input-focus-shadow;
}

/* 暗黑模式下的按钮样式 */
:deep(.button) {
  background-color: $dark-button-bg;
  color: $dark-text-primary;
  border-color: $dark-button-border;
}

:deep(.button:hover) {
  background-color: $dark-button-hover-bg;
  border-color: $dark-button-hover-border;
}

:deep(.button.is-link) {
  background-color: $dark-button-bg;
  color: $dark-text-primary;
  border-color: $dark-button-border;
}

:deep(.button.is-link:hover) {
  background-color: $dark-button-hover-bg;
  border-color: $dark-button-hover-border;
}

/* 暗黑模式下的控制按钮 */
:deep(.control .button) {
  background-color: $dark-button-bg;
  color: $dark-text-primary;
  border-color: $dark-button-border;
}

:deep(.control .button:hover) {
  background-color: $dark-button-hover-bg;
  border-color: $dark-button-hover-border;
}
</style>