<script>
    export let name;
    export let value;
    export let format = null;

    $: formattedValue = format === null ? value : value; // TODO: formatting with d3-format
</script>

<div>
    <h1>{name}</h1>
    <span>{formattedValue}</span>
</div>

<style>
    div {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 1rem 1rem;
    }
    h1 {
        font-size: 12pt;
    }
    span {
        font-size: 24pt;
    }
</style>
