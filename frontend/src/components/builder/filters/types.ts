import type { Dimension } from "src/schema";

type FilterRangeValue = number | Date | null;
type FilterRange = [FilterRangeValue, FilterRangeValue];

export type FilterValue = string | number | Date;

interface RangeFilterQuery {
    range: FilterRange;
    values?: any
}

interface ValuesFilterQuery {
    values: FilterValue[];
    range?: any
}

export interface FilterState {
    range: FilterRange | null;
    values: Set<FilterValue> | null;
}

export type FilterQuery = RangeFilterQuery | ValuesFilterQuery;

export interface FilterInfoResponse {
    dimension: Dimension;
    info: FilterInfo;
}

export interface FilterInfo {
    range: FilterRange | null;
    values: FilterValue[] | null;
}

export interface Filter extends FilterInfoResponse {
    state: FilterState;
    query: FilterQuery | null;
}
