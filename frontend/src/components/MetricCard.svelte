<script lang="ts">
    import type { Calculation } from "src/schema";

    export let metric: Calculation;
    $: ({ name, description } = metric);
</script>

<div class="card metric">
    <div class="body">
        <div class="name">{name}</div>
        <div class="sub">by 38 dimensions</div>
    </div>
</div>

<style lang="scss">
    @import "../styles/colors.scss";
    .sub {
        color: $text-muted;
        font-size: 12pt;
        white-space: nowrap;
    }
    .name {
        white-space: nowrap;
    }
</style>
