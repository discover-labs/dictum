import type { Filter, FilterValue } from "./filters/types";

export function compileFilter(filter: Filter) {
    const query = filter.query;
    if (query === null || filter.info.values.length === Array.from(query.values).length) {
        return null;
    }
    if (typeof query.values !== "undefined") {
        return compileValuesQuery(filter.dimension.id, query.values);
    }
}

function compileFilterValue(value: FilterValue) {
    if (typeof value === "string") {
        return `'${value}'`
    }
    return `${value}`;
}

function compileFilterValues(values: FilterValue[]) {
    const commas = values.map(compileFilterValue).join(", ");
    return `(${commas})`
}

function compileValuesQuery(id: string, values: FilterValue[]) {
    const enumeration = compileFilterValues(values);
    if (enumeration === '()') {
        return 'false';
    }
    return `:${id} IN ${enumeration}`;
}
