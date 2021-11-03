<script lang="ts">
    import BigNumbers from "./BigNumbers.svelte";
    import TableDisplay from "./TableDisplay.svelte";
    import type { QueryResult } from "src/schema";

    export let queryResult: QueryResult;
    $: data = queryResult.data;
    $: meta = queryResult.metadata.columns;
</script>

{#if queryResult.data.length === 1}
    <BigNumbers data={data[0]} {meta} />
{:else if queryResult.data.length > 1}
    <TableDisplay {data} {meta} />
{/if}
