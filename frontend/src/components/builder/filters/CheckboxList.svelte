<script lang="ts">
    import Checkbox from "./Checkbox.svelte";
    import { createEventDispatcher } from "svelte";

    export let options: any[];
    export let checked: Set<any>;

    $: all = options.length === Array.from(checked).length;

    const dispatch = createEventDispatcher();
    const handleAll = () => {
        if (all) {
            dispatch("uncheckAll");
        } else {
            dispatch("checkAll");
        }
    };
</script>

<div>
    <Checkbox label="(All)" checked={all} on:toggle={handleAll} />
    {#each options as label}
        <Checkbox {label} checked={checked.has(label)} on:toggle />
    {/each}
</div>
