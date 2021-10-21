<script lang="ts">
    import SidebarButton from "./SidebarButton.svelte";
    export let id: string;
    export let name: string;
    export let description: string | null;
</script>

<div class="sidebar-calculation">
    <span class="name noselect">{name}</span>
    <div class="actions">
        {#if description !== null}
            <SidebarButton label="?" tooltip={description} />
        {/if}
        <SidebarButton label="+" />
    </div>
</div>

<style>
    .sidebar-calculation {
        display: flex;
        align-items: center;
        color: black;
        fill-opacity: 70%;
        padding: 0.1rem 0.5rem;
        margin: 0.5rem 0.5rem;
        cursor: default;
        border-bottom: 1px solid white;
    }
    .name {
        -moz-user-select: none;
        -webkit-user-select: none;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        min-width: 0;
        flex: 1;
    }
    .actions {
        display: none;
    }
    .sidebar-calculation:hover > .actions {
        display: inherit;
    }
</style>
