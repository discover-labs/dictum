<script lang="ts">
    import { createEventDispatcher } from "svelte";
    export let label: string;
    export let checked: boolean;

    const dispatch = createEventDispatcher<{ toggle: { label: string } }>();
    const toggle = () => dispatch("toggle", { label });
</script>

<div>
    <label><input type="checkbox" on:change={toggle} {checked} />{label}</label>
</div>

<style>
    input {
        pointer-events: none;
    }
</style>
