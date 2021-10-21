<script lang="ts">
    export let label: string;
    export let tooltip: string | null = null;
</script>

<button data-tooltip={tooltip}>{label}</button>

<style>
    button {
        background: white;
        cursor: pointer;
        border: none;
        outline: none;
        margin: 0 0.1rem;
    }
</style>
