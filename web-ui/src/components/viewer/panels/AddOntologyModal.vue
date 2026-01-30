<template>
  <cytomine-modal :active="active" title="Add terms to image" @close="$emit('close')">
    <b-message v-if="errorOntologies" type="is-danger" has-icon icon-size="is-small">
      <h2> {{ $t('error') }} </h2>
      <p> {{ $t('unexpected-error-info-message') }} </p>
    </b-message>
    <template v-else>
      <b-field label="Terms">
        <b-select v-model="selectedOntology" placeholder="Select terms by name" :disabled="loadingOntologies"
          :loading="loadingOntologies">
          <option :value="null">
            Select terms
          </option>
          <option v-for="ontology in availableOntologies" :value="ontology.id" :key="ontology.id"
            v-show="!isOntologyAlreadyAdded(ontology.id)">
            {{ ontology.name }}
          </option>
        </b-select>
      </b-field>
    </template>

    <template #footer>
      <button class="button" type="button" @click="$emit('close')" :disabled="savingOntology">
        {{ $t('button-cancel') }}
      </button>
      <button v-if="!errorOntologies && selectedOntology" class="button is-link"
        :class="{ 'is-loading': savingOntology }" :disabled="loadingOntologies || savingOntology"
        @click="addOntologyToImage">
        {{ $t('button-add') }}
      </button>
    </template>
  </cytomine-modal>
</template>

<script>
import CytomineModal from '@/components/utils/CytomineModal';
import { OntologyCollection } from '@/api';

export default {
  name: 'add-ontology-modal',
  components: { CytomineModal },
  props: {
    active: Boolean,
    index: String
  },
  data() {
    return {
      loadingOntologies: true,
      errorOntologies: false,
      ontologies: null,
      selectedOntology: null,
      savingOntology: false
    };
  },
  computed: {
    imageModule() {
      return this.$store.getters['currentProject/imageModule'](this.index);
    },
    imageWrapper() {
      return this.$store.getters['currentProject/currentViewer'].images[this.index];
    },
    imageOntologies() {
      return this.imageWrapper.ontologies || [];
    },
    availableOntologies() {
      if (!this.ontologies) return [];
      return this.ontologies.filter(ont => !this.isOntologyAlreadyAdded(ont.id));
    }
  },
  watch: {
    active: {
      handler: async function (val) {
        if (val) {
          if (this.loadingOntologies) {
            try {
              this.ontologies = (await OntologyCollection.fetchAll({ light: true })).array;
              this.ontologies.sort((a, b) => a.name.localeCompare(b.name));
              this.loadingOntologies = false;
            } catch (error) {
              console.log(error);
              this.errorOntologies = true;
            }
          }
          this.selectedOntology = null;
          this.savingOntology = false;
        }
      }
    }
  },
  methods: {
    isOntologyAlreadyAdded(ontologyId) {
      return this.imageOntologies.some(ont => ont.id === ontologyId);
    },
    async addOntologyToImage() {
      if (!this.selectedOntology) return;
      this.savingOntology = true;
      try {
        await this.$store.dispatch(this.imageModule + 'addOntologyToImage', this.selectedOntology);
        this.$notify({ type: 'success', text: this.$t('notif-success-add-ontology-to-image') });
        this.$emit('close');
      } catch (error) {
        console.log(error);
        this.$notify({ type: 'error', text: this.$t('notif-error-add-ontology-to-image') });
      } finally {
        this.savingOntology = false;
      }
    }
  }
};
</script>