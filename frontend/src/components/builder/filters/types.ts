import type { Dimension } from "src/schema";

type FilterRangeValue = number | Date | null;
type FilterRange = [FilterRangeValue, FilterRangeValue];

interface RangeFilterInfo {
    range: FilterRange;
}

export type FilterValue = string | number | Date;

interface ValuesFilterInfo {
    values: FilterValue[];
}

export interface FilterState {
    range: FilterRange | null;
    values: Set<FilterValue> | null;
}

interface FilterQuery {
    query: RangeFilterInfo | ValuesFilterInfo;
}

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
