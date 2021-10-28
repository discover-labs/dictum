<script lang="ts">
    import type { Metric } from "src/schema";
    import DimensionsDropdown from "./DimensionsDropdown.svelte";

    export let metric: Metric;
    $: ({ name, description, dimensions } = metric);
    let dropdown = false;

    function toggleDropdown() {
        dropdown = !dropdown;
    }
    function dropdownOff() {
        setTimeout(() => (dropdown = false), 10);
    }
</script>

<div class="card metric">
    <div class="body">
        <div class="name">{name}</div>
        <div
            class="sub"
            tabindex="-1"
            on:click={toggleDropdown}
            on:blur={dropdownOff}
        >
            <span>by {dimensions.length} dimensions</span><i
                class="arrow-down"
            />
        </div>
        {#if dropdown}
            <DimensionsDropdown {dimensions} />
        {/if}
    </div>
</div>

<style lang="scss">
    @import "../styles/colors.scss";
    .sub {
        color: $text-muted;
        font-size: 12pt;
        white-space: nowrap;
        display: flex;
        flex-direction: row;
        align-items: center;
        cursor: pointer;
        white-space: nowrap;
    }
    .name {
        white-space: nowrap;
        margin-bottom: 5pt;
    }
    .arrow-down {
        margin-left: 0.4rem;
        width: 0;
        height: 0;
        border-left: 4pt solid transparent;
        border-right: 4pt solid transparent;
        border-top: 4pt solid $text-muted;
        font-size: 0;
        line-height: 0;
    }
</style>
