<template>
    <div class="input-fields">
        <InputField label="Problem file:" v-model="instanceFile" type="file" accept=".pddl" />
        <InputField label="Domain file:" v-model="domainFile" type="file" accept=".pddl" />
        <InputField label="Horizon:" v-model="horizon" type="number" placeholder="Enter horizon" />
        <DropdownField
            label="Encoding:"
            :options="Object.values(EncodingType)"
            v-model="encoding"
            :isMultiple="false"
        />
        <InputField label="Number of sets:" v-model="numberOfSets" type="number" />
    </div>
    <Divider/>
    <div class="search-fields">
        <DropdownField
            label="Facet:"
            :options="Object.values(SelectionState)"
            v-model="selectedFacetState"
            :isMultiple="true"
        />
        <DropdownField
            label="Action:"
            :options="Object.values(ActionType)"
            v-model="selectedActionType"
            :isMultiple="true"
        />
        <DropdownField
            label="Constants:"
            :options="allConstants"
            v-model="selectedConstants"
            :isMultiple="true"
        />
        <DropdownField
            label="Timesteps:"
            :options="allTimesteps"
            v-model="selectedTimesteps"
            :isMultiple="true"
        />
    </div>
</template>

<script setup lang="ts">
import { EncodingType } from '@/models/EncodingType';
import { SelectionState } from '@/models/SelectionState';
import { ActionType } from '@/models/ActionType';
import { computed, ref } from 'vue';
import InputField from '@/components/InputField.vue';
import DropdownField from '@/components/DropdownField.vue';
import Divider from '@/components/Divider.vue';
import type { Facet } from '@/models/Facet';

const instanceFile = ref('');
const domainFile = ref('');
const horizon = ref<number>(0);
const encoding = ref<EncodingType[]>([EncodingType.Exact])
const numberOfSets = ref<number | undefined>(undefined);
const facets = ref<Facet[]>([]);

const selectedFacetState = ref<SelectionState[]>([])
const selectedActionType = ref<ActionType[]>([])
const selectedConstants = ref<string[]>([])
const selectedTimesteps = ref<number[]>([]);

const allConstants = computed(() => {
    const constantsSet = new Set<string>();
    for (const facet of facets.value) {
        if (facet.constant1) constantsSet.add(facet.constant1);
        if (facet.constant2) constantsSet.add(facet.constant2);
    }
    return Array.from(constantsSet).sort();
});

const allTimesteps = computed(() => {
    const timestepSet = new Set<number>();
    for (const facet of facets.value) {
        timestepSet.add(facet.timestep);
    }
    return Array.from(timestepSet).sort((a, b) => a - b);
});
</script>

<style scoped>
.input-fields {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
}
.search-fields {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
}
</style>