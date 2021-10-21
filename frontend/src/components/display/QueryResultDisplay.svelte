<script lang="ts">
    import BigNumbers from "./BigNumbers.svelte";
    import TableDisplay from "./TableDisplay.svelte";
    import { getFormatters } from "../format";
    import type { Calculation, QueryResult } from "src/schema";

    export let queryResult: QueryResult;
    $: data = queryResult.data;
    $: formatters = getFormatters(queryResult.metadata);
    $: meta = queryResult.metadata.columns.reduce(
        (acc: object, val: Calculation) =>
            Object.assign(acc, { [val.id]: val }),
        {}
    );
</script>

{#if queryResult.data.length === 1}
    <BigNumbers {data} {formatters} {meta} />
{:else if queryResult.data.length > 1}
    <TableDisplay {data} {formatters} {meta} />
{/if}
