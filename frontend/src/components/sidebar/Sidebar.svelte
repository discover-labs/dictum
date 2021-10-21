<script lang="ts">
    import type { Store } from "src/schema";

    import SidebarCalculationDisplay from "./SidebarCalculationDisplay.svelte";

    export let store: Store;

    let searchQuery = "";
</script>

<div class="query-sidebar">
    <div class="search">
        <input bind:value={searchQuery} placeholder="Search..." />
    </div>
    <div class="calculations">
        <ul>
            {#each store.measures as { id, name, description } (id)}
                <SidebarCalculationDisplay {id} {name} {description} />
            {/each}
        </ul>
    </div>
    <div class="calculations">&nbsp;</div>
</div>

<style>
    .query-sidebar {
        height: 100vg;
        width: 15rem;
        border-right: 1px solid lightgray;

        display: flex;
        flex-direction: column;
    }

    .calculations {
        border-bottom: 1px solid lightgray;
        flex-basis: 100%;
        overflow-y: scroll;
    }

    ul {
        list-style-type: none;
        padding: 0;
    }
    .search {
        border-bottom: 1px solid lightgray;
        padding: 0.5rem;
    }
    .search > input {
        width: 100%;
        border: none;
        outline: none;
    }
</style>
