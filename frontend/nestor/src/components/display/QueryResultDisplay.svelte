<script>
    import BigNumbers from "./BigNumbers.svelte";
    import TableDisplay from "./TableDisplay.svelte";

    export let queryResult;
</script>

{#if queryResult.data.length === 1}
    <BigNumbers {queryResult} />
{:else if queryResult.data.length > 1}
    <TableDisplay {queryResult} />
{/if}
