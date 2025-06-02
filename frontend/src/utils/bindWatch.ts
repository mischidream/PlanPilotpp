import { watch, type Ref } from 'vue';

export function bindWatch<T>(source: Ref<T>, setter: (val: T) => void, options = {}) {
  watch(source, setter, options);
}
