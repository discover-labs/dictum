<script lang="ts">
    import type { QueryResult, Store } from "src/schema";
    import Sidebar from "../components/sidebar/Sidebar.svelte";
    import { Server } from "../graphql";

    let queryResult: QueryResult | null = null;
    // let store: Store | null = null;

    const server = new Server();
    const storeQuery = `
    query {
        store {
            measures { id name description }
            dimensions { id name description }
        }
    }
    `;
</script>

<div class="query-page">
    {#await server.request(storeQuery)}
        Loading...
    {:then data}
        <Sidebar store={data.store} />
        <div class="builder">&nbsp;</div>
    {/await}
</div>

<style>
    .query-page {
        height: 100%;
        display: flex;
        flex-direction: row;
    }
    .builder {
        background-color: whitesmoke;
        flex: 1 0 auto;
    }
</style>
