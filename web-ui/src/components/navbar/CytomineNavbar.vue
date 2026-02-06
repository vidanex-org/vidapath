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
  <nav class="navbar" role="navigation">
    <div class="navbar-brand">
      <router-link :to="projects" exact class="navbar-item">
        <div class="logo-container">
          <img src="@/assets/icon.svg" id="logo" alt="VidaPath">
          <h1 class="brand">VidaPath</h1>
        </div>
      </router-link>
    </div>
    <div id="topMenu" class="navbar-menu" :class="{ 'is-active': openedTopMenu }">
      <div v-if="!$keycloak.hasTemporaryToken" class="navbar-start">
        <!-- <navbar-dropdown
      icon="fa-folder-open"
      v-if="this.nbActiveProjects > 0"
      :title="$t('workspace')"
      :listPathes="['/project/']">
        <navigation-tree />
      </navbar-dropdown> -->
        <router-link to="/projects" class="navbar-item">
          <i class="fas fa-list-alt"></i>
          <span>{{ projectsLabel }}</span>
        </router-link>
        <router-link to="/ontology" class="navbar-item">
          <i class="fa fa-hashtag"></i>
          <span>Terms</span>
        </router-link>
        <router-link to="/storage" class="navbar-item">
          <i class="fas fa-upload"></i>
          <span>Upload</span>
        </router-link>
        <router-link to="/ai" class="navbar-item">
          <i class="fas fa-robot"></i>
          <span>AI</span>
        </router-link>
        <!-- <router-link v-if="appEngineEnabled" to="/apps" class="navbar-item">
        <i class="fas fa-code"></i>
        {{ $t('app-engine.applications') }}
      </router-link>
      <router-link v-if="currentUser.adminByNow" to="/admin" class="navbar-item">
        <i class="fas fa-wrench"></i>
        {{ $t('admin-menu') }}
      </router-link> -->
      </div>

      <div v-if="showPatientInfo" class="patient-info">
        <div class="patient-details">
          <span v-if="currentProject.patientName" class="patient-field">PATIENT: {{ currentProject.patientName }}</span>
          <span v-if="currentProject.patientId" class="patient-field">PATIENT ID: {{ currentProject.patientId }}</span>
          <span v-if="currentProject.patientAge" class="patient-field">AGE: {{ currentProject.patientAge }}</span>
          <span v-if="currentProject.patientAge" class="patient-field">GENDER: {{ currentProject.patientSex }}</span>
        </div>
      </div>

      <div class="navbar-end">
        <!-- 显示患者信息 -->

        <!-- <cytomine-searcher /> -->
        <!-- TODO IAM -->
        <navbar-dropdown v-if="!$keycloak.hasTemporaryToken" icon="fa-user" :title="currentUser.name"
          :listPathes="['/account']">
          <router-link to="/account" class="navbar-item">
            <i class="fas fa-user fa-xs"></i>
            {{ $t('account') }}
          </router-link>
          <!-- <router-link to="/activity" class="navbar-item">
            <span class="icon"><i class="fas fa-history fa-xs"></i></span> {{ $t('activity-history') }}
          </router-link> -->
          <!-- <template v-if="currentUser.admin">
            <a v-if="!currentUser.adminByNow" class="navbar-item" @click="openAdminSession()">
              <span class="icon"><i class="fas fa-star fa-xs"></i></span> {{ $t('open-admin-session') }}
            </a>
            <a v-else class="navbar-item" @click="closeAdminSession()">
              <span class="icon"><i class="far fa-star fa-xs"></i></span> {{ $t('close-admin-session') }}
            </a>
          </template> -->
          <a class="navbar-item" @click="logout()">
            <i class="fas fa-power-off fa-xs"></i>
            {{ $t('logout') }}
          </a>
        </navbar-dropdown>

        <navbar-dropdown icon="fa-question-circle" :title="$t('help')">
          <a class="navbar-item" @click="openHotkeysModal()">
            <i class="far fa-keyboard fa-xs"></i>
            {{ $t('shortcuts') }}
          </a>
          <a class="navbar-item" @click="openAboutModal()">
            <i class="fas fa-info-circle fa-xs"></i>
            About
          </a>
        </navbar-dropdown>
      </div>
    </div>
    <div class="hidden" v-shortkey.once="openHotkeysModalShortcut" @shortkey="openHotkeysModal"></div>
  </nav>
</template>

<script>
import { get } from '@/utils/store-helpers';
import { mapGetters } from 'vuex';
import { changeLanguageMixin } from '@/lang.js';

import NavbarDropdown from './NavbarDropdown';
import NavigationTree from './NavigationTree';
import HotkeysModal from './HotkeysModal';
import AboutCytomineModal from './AboutCytomineModal';
import CytomineSearcher from '@/components/search/CytomineSearcher';
import constants from '@/utils/constants.js';
import shortcuts from '@/utils/shortcuts.js';

export default {
  name: 'cytomine-navbar',
  components: {
    NavbarDropdown,
    NavigationTree,
    CytomineSearcher
  },
  mixins: [changeLanguageMixin],
  data() {
    return {
      openedTopMenu: false,
      hotkeysModal: null,
      appEngineEnabled: constants.APPENGINE_ENABLED,
      aboutModal: null
    };
  },
  computed: {
    ...mapGetters('serverConfig', ['isFolderBasedEnabled']),
    currentUser: get('currentUser/user'),
    currentProject: get('currentProject/project'),
    nbActiveProjects() {
      return Object.keys(this.$store.state.projects).length;
    },
    openHotkeysModalShortcut() {
      return shortcuts['general-shortcuts-modal'];
    },
    showPatientInfo() {
      // 检查是否在Viewer页面并且当前项目有患者信息
      return this.$route.path.includes('/image/') && this.currentProject &&
        (this.currentProject.patientName || this.currentProject.patientId || this.currentProject.patientAge) &&
        !this.$keycloak.hasTemporaryToken;
    },
    projects() {
      return this.$keycloak.hasTemporaryToken ? `/projects?access_token=${this.$keycloak.temporaryToken}` : '/projects';
    },
    projectsLabel() {
      // Dynamically return "Folders" or "Cases" based on server config
      return this.isFolderBasedEnabled ? 'Folders' : 'Cases';
    }
  },
  watch: {
    $route() {
      this.openedTopMenu = false;
    }
  },
  methods: {
    // required to use programmatic modal for correct display in IE11
    openHotkeysModal() {
      if (!this.hotkeysModal) {
        this.hotkeysModal = this.$buefy.modal.open({
          parent: this,
          component: HotkeysModal,
          hasModalCard: true,
          onCancel: () => this.hotkeysModal = null,
        });
      }
    },
    openAboutModal() {
      this.$buefy.modal.open({
        parent: this,
        component: AboutCytomineModal,
        hasModalCard: true
      });
    },
    // ---

    async openAdminSession() {
      try {
        await this.$store.dispatch('currentUser/openAdminSession');
        this.$router.push('/admin');
      } catch (error) {
        console.log(error);
      }
    },
    async closeAdminSession() {
      try {
        await this.$store.dispatch('currentUser/closeAdminSession');
        if (this.$router.currentRoute.path === '/') {
          this.$router.push('/projects');
        } else {
          this.$router.push('/');
        }
      } catch (error) {
        console.log(error);
      }
    },

    async logout() {
      try {
        this.$store.dispatch('logout');
        this.changeLanguage();
        await this.$keycloak.logout();
      } catch (error) {
        console.log(error);
        this.$notify({ type: 'error', text: this.$t('notif-error-logout') });
      }
    }
  }
};
</script>

<style lang="scss">
@import '../../assets/styles/dark-variables.scss';

.logo-container {
  color: white;
  display: flex;
  align-items: center;
  height: 30px;
}

.navbar {
  font-weight: 600;
  z-index: 500;
  background-color: $navbar-bg-primary !important;
  color: $navbar-text-color !important;

  .fas,
  .far {
    padding-right: 0.5rem;
  }

  .navbar-brand {
    .brand {
      color: $navbar-text-color !important;
    }
  }

  .navbar-item,
  .navbar-link {
    background-color: transparent !important;
    color: $navbar-text-color !important;
  }

  .navbar-item:hover,
  .navbar-link:hover {
    background-color: $navbar-bg-secondary !important;
    color: $navbar-text-color !important;
  }

  .navbar-dropdown .navbar-item:hover {
    background-color: $navbar-bg-secondary !important;
    color: $navbar-text-color !important;
  }
}

.patient-info {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-grow: 1;
  padding-right: 4rem;
}

.patient-details {
  display: flex;
  gap: 2rem;
  align-items: center;
  background-color: transparent;
  padding: 0.5rem 1rem;
  border-radius: 4px;
}

.patient-feild {
  font-weight: bold;
  font-size: 1.1rem;
}

/* Special styling for IE */
@media screen and (-ms-high-contrast: active),
(-ms-high-contrast: none) {
  #logo {
    height: 40px;
    max-height: none;
  }
}
</style>