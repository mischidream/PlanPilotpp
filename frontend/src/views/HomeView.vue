<template>
    <div class="input-fields">
        <InputField label="Problem file:" v-model="instanceFile" type="file" accept=".pddl" />
        <InputField label="Domain file:" v-model="domainFile" type="file" accept=".pddl" />
        <InputField label="Horizon:" v-model="horizon" type="number" placeholder="Enter horizon" />
        <DropdownField
            label="Encoding:"
            :options="Object.values(EncodingType)"
            v-model="encoding"
        />
        <InputField label="Number of sets:" v-model="numberOfSets" type="number" />
    </div>
</template>

<script setup lang="ts">
import { EncodingType } from '@/models/EncodingType';
import { ref } from 'vue';
import InputField from '@/components/InputField.vue';
import DropdownField from '@/components/DropdownField.vue';

const instanceFile = ref(''); // Renamed to match UserInput
const domainFile = ref('');
const horizon = ref<number>(0); // Horizon is a number
const encoding = ref<EncodingType>(EncodingType.Exact);
const numberOfSets = ref<number | undefined>(undefined);
</script>

<style scoped>
.input-fields {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    justify-content: space-between;
}
</style>