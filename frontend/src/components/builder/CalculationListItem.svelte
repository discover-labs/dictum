<script>
    import { createEventDispatcher } from "svelte";
    const dispatch = createEventDispatcher();

    export let id;
    export let name;
    export let description;
    export let selected;

    const clickItem = () => dispatch("clickItem", { id });
    const hoverItem = () => dispatch("hoverItem", { id });
</script>

<div
    class="wrapper"
    class:selected
    on:click={clickItem}
    on:mouseover={hoverItem}
    on:focus={hoverItem}
>
    <div class="header">
        <span>{@html name}</span>
    </div>
    {#if description}
        <p class="description">{description}</p>
    {/if}
</div>

<style>
    .wrapper {
        border: 1px solid #e5e5e5;
        border-collapse: collapse;
        padding: 12pt 8pt;
        overflow-y: scroll;
        margin: 0;
        margin-bottom: -1px;
        background-color: white;
    }
    .selected {
        background-color: lightblue;
    }
    .header {
        font-size: 14pt;
    }
    .description {
        font-size: 11pt;
        color: #aaa;
        max-width: 100%;
        text-overflow: ellipsis;
        overflow-x: hidden;
        white-space: nowrap;
        margin: 0;
        margin-top: 5pt;
    }
</style>
