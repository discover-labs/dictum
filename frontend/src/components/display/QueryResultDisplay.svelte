<script lang="ts">
    import type { QueryResult } from "../../schema";
    import BigNumbers from "./BigNumbers.svelte";
    import TableDisplay from "./TableDisplay.svelte";

    export let queryResult: QueryResult;
</script>

{#if queryResult.data.length === 1}
    <BigNumbers {queryResult} />
{:else if queryResult.data.length > 1}
    <TableDisplay {queryResult} />
{/if}
