<script lang="ts">
    import { createEventDispatcher } from "svelte";
    export let id: string;
    export let name: string;

    const dispatch = createEventDispatcher();
    const close = () => dispatch("closeItemClick", { id });
</script>

<div class="calculation">
    <mark><span>{name}</span><button on:click={close}>x</button></mark>
</div>

<style>
    .calculation {
        display: inline-block;
        margin-left: 0.5rem;
    }
</style>
