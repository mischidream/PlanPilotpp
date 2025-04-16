<template>
    <div class="input-fields">
        <InputField label="Problem file:" v-model="instanceFile" type="file" accept=".pddl" />
        <InputField label="Domain file:" v-model="domainFile" type="file" accept=".pddl" />
        <Button label="Start" type="submit"></Button>
    </div>
</template>

<script setup lang="ts">
import InputField from '@/components/InputField.vue';
import Button from '@/components/Button.vue';
import { ref } from 'vue';

const instanceFile = ref<File | null>(null);
const domainFile = ref<File | null>(null);
</script>

<style scoped>
.input-fields {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
}
.input-fields .button{
    align-self: flex-end;
    min-height: 40px;
}
</style>