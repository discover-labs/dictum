<script lang="ts">
    import type { Dimension } from "src/schema";

    export let dimensions: Dimension[];
</script>

<div class="dimensions-dropdown card dimension">
    {#each dimensions as { name }}
        <div class="dimensions-dropdown-item">
            {name}
        </div>
    {/each}
</div>

<style lang="scss">
    @import "../styles/colors.scss";
    .card {
        padding: 0;
    }
    .dimensions-dropdown {
        position: absolute;
        display: flex;
        flex-direction: column;
        max-height: 30rem;
        overflow-y: scroll;
    }

    .dimensions-dropdown-item {
        padding: 5pt 10pt;
        margin: 0;
        background-color: white;
        font-size: 12pt;
        cursor: pointer;

        &:hover {
            background-color: $green;
            color: white;
        }
    }
</style>
