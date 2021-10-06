<script>
    import { createEventDispatcher } from "svelte";
    export let id;
    export let name;
    export let type;

    const dispatch = createEventDispatcher();
    const close = (event) => dispatch("closeItemClick", { id });
</script>

<div class="calculation">
    <mark><span>{name} ({type})</span><button on:click={close}>x</button></mark>
</div>

<style>
    .calculation {
        display: inline-block;
        margin-left: 0.5rem;
    }
</style>
